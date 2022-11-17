from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Generator
from uuid import uuid4
import grpc
from protos.message_board.message_board_pb2_grpc import MessageBoardServicer, add_MessageBoardServicer_to_server
from protos.message_board.message_board_pb2 import Cookie, Credentials, Post, PostAmount, ReadPost, WritePost
from google.protobuf.empty_pb2 import Empty
from Exceptions import InvalidArgument, NotFound, PermissionDenied, Unauthenticated

def wrap_exceptions(func):

    @wraps(func)
    def call(self, request, context):
        try:
            print("calling function")
            return func(self, request, context)
        except Unauthenticated:
            context.set_code(grpc.StatusCode.UNAUTHENTICATED)
            raise
        except InvalidArgument:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            raise
        except NotFound:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            raise
        except PermissionDenied:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            raise
    
    return call
        

class MessageBoardImpl(MessageBoardServicer):

    def __init__(self):
        super().__init__()
        self.active: dict[str, str] = {}
        self.passwords: dict[str, str] = {}
        self.messages: dict[str, list[str]] = {}

    @wrap_exceptions
    def register(self, request: Credentials, context) -> Cookie:
        if request.username is None: raise InvalidArgument("Please enter a username!")
        if request.password is None: raise InvalidArgument("Please enter a password!")
        self.passwords[request.username] = request.password # exploit by setting new password for existing user
        self.messages[request.username] = []
        return Empty()

    @wrap_exceptions
    def login(self, request: Credentials, context):
        if request.username is None: raise InvalidArgument("Please enter a username!")
        if request.password is None: raise InvalidArgument("Please enter a password!")
        if request.username not in self.passwords: raise NotFound("User is not registered!")
        if self.passwords[request.username] != request.password: raise Unauthenticated("Password is wrong!")
        cookie = uuid4().hex
        self.active[cookie] = request.username
        return Cookie(cookie=cookie)

    @wrap_exceptions
    def logout(self, request: Cookie, context):
        if request.cookie is None: raise InvalidArgument("Please enter a cookie!")
        if request.cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        del self.active[request.cookie]
        return Empty()

    @wrap_exceptions
    def get_posts(self, request: Cookie, context) -> PostAmount:
        if request.cookie is None: raise InvalidArgument("Please enter a cookie!")
        if request.cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        username = self.active[request.cookie]
        return PostAmount(amount=len(self.messages[username]))

    @wrap_exceptions
    def read(self, request: ReadPost, context) -> Post:
        if request.cookie is None or (cookie := request.cookie.cookie) is None: raise InvalidArgument("Please enter a cookie!")
        if cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        username = self.active[cookie]
        index = request.index or 0
        return Post(text=self.messages[username][index])

    @wrap_exceptions
    def read_all(self, request: Cookie, context) -> Generator[Post, None, None]:
        if request.cookie is None: raise InvalidArgument("Please enter a cookie!")
        if request.cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        username = self.active[request.cookie]
        for msg in self.messages[username]:
            yield Post(text = msg)
      
    @wrap_exceptions  
    def write(self, request: WritePost, context):
        if request.cookie is None or (cookie := request.cookie.cookie) is None: raise InvalidArgument("Please enter a cookie!")
        if cookie not in self.active: raise Unauthenticated("Cookie is not authenticated!")
        if request.post is None or (text := request.post.text) is None: raise InvalidArgument("Please enter a text!")
        username = self.active[cookie]
        if len(self.messages[username]) >= 50: raise PermissionDenied("Can not post any more messages with this account!")
        self.messages[username].append(text)
        return Empty()
    
def serve():
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    add_MessageBoardServicer_to_server(MessageBoardImpl(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    print("Starting server...")
    serve()
