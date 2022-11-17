from argparse import ArgumentError
import grpc
from protos.message_board.message_board_pb2 import Cookie, Credentials, Post, ReadPost, WritePost
from protos.message_board.message_board_pb2_grpc import MessageBoardStub


class LiveClient:

    def __init__(self):
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = MessageBoardStub(channel)

    def register(self, username: str, password: str):
        creds = Credentials(username=str(username), password=str(password))
        self.stub.register(creds)

    def login(self, username: str, password: str):
        creds = Credentials(username=str(username), password=str(password))
        resp: Cookie = self.stub.login(creds)
        return resp.cookie

    def logout(self, cookie: str):
        cookie = Cookie(cookie=cookie)
        self.stub.logout(cookie)

    def write(self, cookie: str, text: str):
        cookie = Cookie(cookie = cookie)
        post = Post(text = text)
        writePost = WritePost(cookie = cookie, post = post)
        self.stub.write(writePost)

    def read_all(self, cookie: str):
        cookie = Cookie(cookie = cookie)
        for resp in self.stub.read_all(cookie):
            yield resp.text

    def read(self, cookie: str, index: int):
        cookie = Cookie(cookie = cookie)
        readPost = ReadPost(cookie = cookie, index = index)
        resp: Post = self.stub.read(readPost)
        return resp.text

    def interactive(self):
        while cmd := input("cmd: "):
            print(eval(cmd))

def print_space(*args):
    print("-----------------")
    print(*args)
    print("-----------------")
    
if __name__ == "__main__":
    c = LiveClient()
    c.register("Hello", "World")
    cookie: str = c.login("Hello", "World")
    print(f"{cookie=}")
    c.write(cookie, "Hello")
    c.write(cookie, "World")
    print(list(c.read_all(cookie)))
    try:
        c.read(cookie, 10)
    except grpc.RpcError as rpc_error:
        print_space(rpc_error)
        print_space(rpc_error.details())
        print_space(status := rpc_error.code())
        print_space(status.name)
        print_space(status.value)
        raise rpc_error

