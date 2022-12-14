from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import logging
import colorlog
from sys import stdout
import sys
from typing import Generator
from uuid import uuid4
import grpc
from protos.message_board.message_board_pb2_grpc import MessageBoardServicer, add_MessageBoardServicer_to_server
from protos.message_board.message_board_pb2 import Cookie, Credentials, Post, PostAmount, ReadPost, WritePost
from google.protobuf.empty_pb2 import Empty
from protos.GrpcExceptions import InvalidArgument, NotFound, PermissionDenied, Unauthenticated


def setup_logger(fileLevel=logging.INFO, outLevel=logging.DEBUG, errLevel=logging.WARN):

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    if fileLevel:
        fileHandler = logging.FileHandler(filename='logs/message_board.log', mode='a', encoding='utf-8', delay=True)
        formatter = logging.Formatter(fmt='%(asctime)s:%(levelname)s:%(threadName)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(fileLevel)
        rootLogger.addHandler(fileHandler)

    if outLevel:
        outHandler = logging.StreamHandler(sys.stdout)
        formatter = colorlog.ColoredFormatter(fmt='%(levelname)s:%(message)s')
        outHandler.setFormatter(formatter)
        outHandler.setLevel(outLevel)
        rootLogger.addHandler(outHandler)

    if errLevel:
        errHandler = logging.StreamHandler(sys.stderr)
        formatter = colorlog.ColoredFormatter(fmt='%(levelname)s:%(message)s')
        errHandler.setFormatter(formatter)
        errHandler.setLevel(errLevel)
        rootLogger.addHandler(errHandler)

    logging.info("Logger setup completed")

def wrap_exceptions(func):

    @wraps(func)
    def call(self, request, context):
        try:
            return func(self, request, context)
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
    
    return call
        

class MessageBoardImpl(MessageBoardServicer):

    def __init__(self):
        super().__init__()
        self.active: dict[str, str] = {}
        self.passwords: dict[str, str] = {}
        self.messages: dict[str, list[str]] = defaultdict(list)
        self.logger = logging.getLogger()

    @wrap_exceptions
    def register(self, request: Credentials, context) -> Cookie:
        self.logger.info("Register Request for username: %s with password: %s", request.username, request.password)
        if request.username is None: raise InvalidArgument("Please enter a username!")
        if request.password is None: raise InvalidArgument("Please enter a password!")
        self.passwords[request.username] = request.password # exploit by setting new password for existing user
        return Empty()

    @wrap_exceptions
    def login(self, request: Credentials, context):
        self.logger.info("Login Request for username: %s with password: %s", request.username, request.password)
        if request.username is None: raise InvalidArgument("Please enter a username!")
        if request.password is None: raise InvalidArgument("Please enter a password!")
        if request.username not in self.passwords: raise NotFound("User is not registered!")
        if self.passwords[request.username] != request.password: raise Unauthenticated("Password is wrong!")
        cookie = uuid4().hex
        self.active[cookie] = request.username
        return Cookie(cookie=cookie)

    @wrap_exceptions
    def logout(self, request: Cookie, context):
        self.logger.info("Logout Request for cookie: %s", request.cookie)
        if request.cookie is None: raise InvalidArgument("Please enter a cookie!")
        if request.cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        del self.active[request.cookie]
        return Empty()

    @wrap_exceptions
    def get_posts(self, request: Cookie, context) -> PostAmount:
        self.logger.info("GetPosts Request for cookie: %s", request.cookie)
        if request.cookie is None: raise InvalidArgument("Please enter a cookie!")
        if request.cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        username = self.active[request.cookie]
        return PostAmount(amount=len(self.messages[username]))

    @wrap_exceptions
    def read(self, request: ReadPost, context) -> Post:
        self.logger.info("Read Request for cookie: %s and index: %s", request.cookie.cookie, request.index)
        if request.cookie is None or (cookie := request.cookie.cookie) is None: raise InvalidArgument("Please enter a cookie!")
        if cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        username = self.active[cookie]
        index = request.index or 0
        return Post(text=self.messages[username][index])

    @wrap_exceptions
    def read_all(self, request: Cookie, context) -> Generator[Post, None, None]:
        self.logger.info("ReadAll Request for cookie: %s", request.cookie)
        if request.cookie is None: raise InvalidArgument("Please enter a cookie!")
        if request.cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        username = self.active[request.cookie]
        for msg in self.messages[username]:
            yield Post(text = msg)
      
    @wrap_exceptions  
    def write(self, request: WritePost, context):
        self.logger.info("Write Request for cookie: %s and text: %s", request.cookie.cookie, request.post.text)
        if request.cookie is None or (cookie := request.cookie.cookie) is None: raise InvalidArgument("Please enter a cookie!")
        if cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        if request.post is None or (text := request.post.text) is None: raise InvalidArgument("Please enter a text!")
        username = self.active[cookie]
        if len(self.messages[username]) >= 50: raise PermissionDenied("Can not post any more messages with this account!")
        self.messages[username].append(text)
        return Empty()
    
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
    setup_logger()
    serve()
