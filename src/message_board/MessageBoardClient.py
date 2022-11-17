from argparse import ArgumentError
import grpc
from protos.message_board.message_board_pb2 import Cookie, Credentials, Post, ReadPost, WritePost
from protos.message_board.message_board_pb2_grpc import MessageBoardStub


class MessageBoardClient:

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
            try:
                print(eval(cmd))
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
            except Exception as e:
                print(e)

    def init_testuser(self):
        self.register("Test", "test")
        cookie = self.login("Test", "test")
        self.write(cookie, "Hello, World!")
        self.write(cookie, "FooBar")
        return cookie
    
if __name__ == "__main__":
    c = MessageBoardClient()
    c.interactive()

