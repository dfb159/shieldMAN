from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import logging
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
import colorlog
import sys
from typing import Generator
from uuid import uuid4
import grpc
from message_board.Board import Board
from protos.message_board.message_board_pb2_grpc import MessageBoardServicer, add_MessageBoardServicer_to_server
from protos.message_board.message_board_pb2 import Cookie, Credentials, Post, PostCount, BoardAuth, BoardCreate, BoardReadRange, BoardText
from protos.GrpcExceptions import InvalidArgument, NotFound, PermissionDenied, Unauthenticated
from google.protobuf.empty_pb2 import Empty

def setup_logger(fileLevel=logging.INFO, outLevel=logging.DEBUG, errLevel=logging.WARN):

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    if fileLevel is not None:
        fileHandler = logging.FileHandler(filename='logs/message_board.log', mode='a', encoding='utf-8', delay=True)
        formatter = logging.Formatter(fmt='%(asctime)s:%(levelname)s:%(threadName)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(fileLevel)
        rootLogger.addHandler(fileHandler)

    if outLevel is not None:
        outHandler = logging.StreamHandler(sys.stdout)
        formatter = colorlog.ColoredFormatter(fmt='%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s')
        outHandler.setFormatter(formatter)
        outHandler.setLevel(outLevel)
        rootLogger.addHandler(outHandler)

    if errLevel is not None:
        errHandler = logging.StreamHandler(sys.stderr)
        formatter = colorlog.ColoredFormatter(fmt='%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s')
        errHandler.setFormatter(formatter)
        errHandler.setLevel(errLevel)
        rootLogger.addHandler(errHandler)

    logging.info("Logger setup completed")

def wrap_exceptions(func):
    @wraps(func)
    def wrapper(self: "MessageBoardImpl", request, context):
        try:
            return func(self, request, context) or Empty()
        except Unauthenticated:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            self.logger.warning("Unauthenticated")
            raise
        except (InvalidArgument):
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            self.logger.warning("Invalid argument")
            raise
        except NotFound:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            self.logger.warning("Not found")
            raise
        except PermissionDenied:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            self.logger.warning("Permission denied")
            raise
        except Exception as e:
            self.logger.exception(f"{type(e).__name__}: {str(e)}")
            raise
    
    return wrapper

def log(level: int, message: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self: "MessageBoardImpl", request, context):
            self.logger.log(level, message.format(self = self, request = request, context = context))
            return func(self, request, context)
        return wrapper
    return decorator

def null(variable: str, message: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, context):
            r = request
            for v in variable.split("."):
                r = getattr(r, v)
                if r is None: raise InvalidArgument(message)
            return func(self, request, context)
        return wrapper
    return decorator

class MessageBoardImpl(MessageBoardServicer):

    def __init__(self):
        super().__init__()
        self.active: dict[str, str] = {}
        self.passwords: dict[str, str] = {}
        self.boards: dict[str, Board] = defaultdict(Board)
        self.logger = logging.getLogger()

    @wrap_exceptions
    @log(INFO, "Register Request for username: {request.username} with password: {request.password}")
    @null("username", "Please enter a username!")
    @null("password", "Please enter a password!")
    def register(self, request: Credentials, context):
        self.passwords[request.username] = request.password

    @wrap_exceptions
    @log(INFO, "Login Request for username: {request.username} with password: {request.password}")
    @null("username", "Please enter a username!")
    @null("password", "Please enter a password!")
    def login(self, request: Credentials, context) -> Cookie:
        if request.username not in self.passwords: raise InvalidArgument("User is not registered!")
        if self.passwords[request.username] != request.password: raise Unauthenticated("Password is wrong!")
        cookie = uuid4().hex
        self.active[cookie] = request.username
        return Cookie(cookie=cookie)

    @wrap_exceptions
    @log(INFO, "Logout Request for cookie: {request.cookie}")
    @null("cookie", "Please enter a cookie!")
    def logout(self, request: Cookie, context):
        if request.cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        del self.active[request.cookie]

    @wrap_exceptions
    @log(INFO, "GetPosts Request for cookie: {request.cookie}")
    @null("boardid", "Please enter a boardid!")
    @null("cookie", "Please enter a cookie!")
    def get_count(self, request: BoardAuth, context) -> PostCount:
        username = self.get_username(request.cookie)
        board = self.get_board(request.boardid)
        return PostCount(count=board.amount(username))

    @wrap_exceptions
    @log(INFO, "Read Request on board: {request.auth.boardid} for cookie: {request.auth.cookie} and index: {request.auth.index}, count: {request.auth.count}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    @null("count", "Please enter a count!")
    def read(self, request: BoardReadRange, context) -> Generator[Post, None, None]:
        username = self.get_username(request.auth.cookie)
        board = self.get_board(request.auth.boardid)
        index = request.index or 0
        count = request.count
        for msg in board.read(username, index, count):
            yield Post(text = msg)

    @wrap_exceptions
    @log(INFO, "Readall Request on board: {request.auth.boardid} for cookie: {request.auth.cookie}")
    @null("boardid", "Please enter a boardid!")
    @null("cookie", "Please enter a cookie!")
    def read_all(self, request: BoardAuth, context) -> Generator[Post, None, None]:
        username = self.get_username(request.cookie)
        board = self.get_board(request.boardid)
        for msg in board.read_all(username):
            yield Post(text = msg)
      
    @wrap_exceptions
    @log(INFO, "Write Request on board: {request.auth.boardid} for cookie: {request.auth.cookie} and text: {request.text}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    @null("text", "Please enter a text!")
    def write(self, request: BoardText, context):
        cookie = request.auth.cookie
        username = self.get_username(cookie)
        board = self.get_board(request.auth.boardid)
        board.write(username, request.text)
        
    @wrap_exceptions
    @log(INFO, "Create Request for board: {request.auth.boardid} and cookie: {request.auth.cookie}. Board is public = {request.public}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    def create(self, request: BoardCreate, context):
        username = self.get_username(request.auth.cookie)
        self.boards[request.auth.boardid] = Board(request.boardname, username, request.public or True)
        
    @wrap_exceptions
    @log(INFO, "Delete Request for board: {request.boardid} and cookie: {request.cookie}")
    @null("boardid", "Please enter a boardid!")
    @null("cookie", "Please enter a cookie!")
    def delete(self, request: BoardAuth, context):
        username = self.get_username(request.cookie)
        board = self.get_board(request.boardid)
        board.is_owner(username)
        del self.boards[request.boardid]

    @wrap_exceptions
    @log(INFO, "Add Owner Request for board: {request.auth.boardid} and cookie: {request.auth.cookie} for new username: {request.text}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    @null("text", "Please enter a username!")
    def add_owner(self, request: BoardText, context):
        username = self.get_username(request.auth.cookie)
        board = self.get_board(request.auth.boardid)
        board.add_owner(username, request.text)
        
    @wrap_exceptions
    @log(INFO, "Add Reader Request for board: {request.auth.boardid} and cookie: {request.auth.cookie} for new username: {request.text}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    @null("text", "Please enter a username!")
    def add_reader(self, request: BoardText, context):
        username = self.get_username(request.auth.cookie)
        board = self.get_board(request.auth.boardid)
        board.add_reader(username, request.text)
        
    @wrap_exceptions
    @log(INFO, "Remove Owner Request for board: {request.auth.boardid} and cookie: {request.auth.cookie} for new username: {request.text}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    @null("text", "Please enter a username!")
    def remove_owner(self, request: BoardText, context):
        username = self.get_username(request.auth.cookie)
        board = self.get_board(request.auth.boardid)
        board.remove_owner(username, request.text)
        
    @wrap_exceptions
    @log(INFO, "Remove Reader Request for board: {request.auth.boardid} and cookie: {request.auth.cookie} for new username: {request.text}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    @null("text", "Please enter a username!")
    def remove_reader(self, request: BoardText, context):
        username = self.get_username(request.auth.cookie)
        board = self.get_board(request.auth.boardid)
        board.remove_reader(username, request.text)

    @wrap_exceptions
    @log(INFO, "Rename Request for board: {request.auth.boardid} and cookie: {request.auth.cookie} for new boardname: {request.text}")
    @null("auth.boardid", "Please enter a boardid!")
    @null("auth.cookie", "Please enter a cookie!")
    @null("text", "Please enter a username!")
    def rename(self, request: BoardText, context):
        username = self.get_username(request.auth.cookie)
        board = self.get_board(request.auth.boardid)
        board.rename(username, request.text)

    def get_username(self, cookie: str):
        if cookie not in self.active:
            raise Unauthenticated("Cookie is not authenticated!")
        return self.active[cookie]

    def get_board(self, boardid: str):
        if boardid not in self.boards:
            raise InvalidArgument("This board does not exist!")
        return self.boards[boardid]
    
def serve():
    logging.info("server setup")
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    add_MessageBoardServicer_to_server(MessageBoardImpl(), server)
    server.add_insecure_port('[::]:50051')
    try:
        logging.info("server starting")
        server.start()
        logging.info("server running...")
        server.wait_for_termination()
    finally:
        logging.info("server terminated")

if __name__ == "__main__":
    setup_logger(errLevel=None)
    serve()
