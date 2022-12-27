from typing import Generator
import grpc
import asyncio
from protos.message_board.message_board_pb2 import BoardAuth, BoardCreate, BoardExists, BoardReadRange, BoardText, Credentials, PostCount, Text
from protos.message_board.message_board_pb2_grpc import MessageBoardStub

class MessageBoardClient:

    def __init__(self, channel):
        self.stub = MessageBoardStub(channel)

    async def register(self, username: str, password: str):
        creds = Credentials(username=username, password=password)
        await self.stub.register(creds)

    async def login(self, username: str, password: str) -> str:
        creds = Credentials(username=username, password=password)
        resp: Text = await self.stub.login(creds)
        return resp.text

    async def logout(self, cookie: str):
        cookie = Text(text=cookie)
        await self.stub.logout(cookie)

    async def get_count(self, boardid: str, cookie: str) -> int:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        resp: PostCount = await self.stub.get_count(auth)
        return resp.count

    async def read(self, boardid: str, cookie: str, index: int = 0, count: int = 1) -> Generator[str, None, None]:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_range = BoardReadRange(auth=auth, index=index, count=count)
        async for resp in self.stub.read(board_range):
            yield resp.text

    async def read_all(self, boardid: str, cookie: str) -> Generator[str, None, None]:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        async for resp in self.stub.read_all(auth):
            yield resp.text

    async def write(self, boardid: str, cookie: str, text: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=text)
        await self.stub.write(board_text)

    async def create(self, boardid: str, cookie: str, boardname: str, public: bool = True):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_create = BoardCreate(auth=auth, boardname=boardname, public=public)
        await self.stub.create(board_create)

    async def delete(self, boardid: str, cookie: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        await self.stub.delete(auth)

    async def add_owner(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        await self.stub.add_owner(board_text)

    async def add_reader(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        await self.stub.add_reader(board_text)

    async def remove_owner(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        await self.stub.remove_owner(board_text)

    async def remove_reader(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        await self.stub.remove_reader(board_text)

    async def rename(self, boardid: str, cookie: str, boardname: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=boardname)
        await self.stub.rename(board_text)

    async def get_name(self, boardid: str, cookie: str) -> str:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        resp: Text = await self.stub.get_name(auth)
        return resp.text

    async def exists(self, boardid: str, cookie: str) -> bool:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        resp: BoardExists = await self.stub.exists(auth)
        return resp.exists

    def interactive(self):
        while cmd := input("cmd: "):
            try:
                print(eval(cmd))
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
            except Exception as e:
                print(e)

    async def init_testuser(self) -> str:
        await self.register("Test", "test")
        return await self.login("Test", "test")

    async def write_flag(self, username: str, password: str, boardname: str, flag: str):
        await self.register(username, password)
        cookie = await self.login(username, password)
        if not await self.exists(boardname, cookie):
            await self.create(boardname, cookie, boardname)
        await self.write(boardname, cookie, flag)
        await self.logout(cookie)

async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        client = MessageBoardClient(channel)
        await client.register("Test", "test")
        cookie = await client.login("Test", "test")
        if not await client.exists("nice", cookie):
            await client.create("nice", cookie, "nice")
        await client.write("nice", cookie, "-"*10)

        async with asyncio.TaskGroup() as tg: # starts all coroutines and awaits all of them
            for n in range(10):
                tg.create_task(client.write("nice", cookie, f"parallel{n}"))

        async for text in client.read_all("nice", cookie):
            print(text)

        #client.interactive()

if __name__ == "__main__":
    asyncio.run(main())

