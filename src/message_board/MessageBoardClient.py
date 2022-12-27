from typing import Generator
import grpc
import asyncio
from message_board.MessageBoardConnector import MessageBoardConnector
from protos.message_board.message_board_pb2 import BoardAuth, BoardCreate, BoardExists, BoardReadRange, BoardText, Credentials, PostCount, Text
from protos.message_board.message_board_pb2_grpc import MessageBoardStub

class MessageBoardClient(MessageBoardConnector):
    cookie: str | None

    def __init__(self, channel):
        super().__init__(channel)
        self.cookie = None

    async def login(self, username: str, password: str):
        self.cookie = await super().login(username, password)

    async def logout(self):
        await super().logout(self.cookie)
        self.cookie = None

    def get_count(self, boardid: str) -> int:
        return super().get_count(boardid, self.cookie)

    def read(self, boardid: str, index: int = 0, count: int = 1) -> Generator[str, None, None]:
        return super().read(boardid, self.cookie, index, count)

    def read_all(self, boardid: str) -> Generator[str, None, None]:
        return super().read_all(boardid, self.cookie)

    def write(self, boardid: str, text: str):
        return super().write(boardid, self.cookie, text)

    def create(self, boardid: str, boardname: str, public: bool = True):
        return super().create(boardid, self.cookie, boardname, public)

    def delete(self, boardid: str):
        return super().delete(boardid, self.cookie)

    def add_owner(self, boardid: str, username: str):
        return super().add_owner(boardid, self.cookie, username)

    def add_reader(self, boardid: str, cookie: str, username: str):
        return super().add_reader(boardid, self.cookie, username)

    def remove_owner(self, boardid: str, username: str):
        return super().remove_owner(boardid, self.cookie, username)

    def remove_reader(self, boardid: str, username: str):
        return super().remove_reader(boardid, self.cookie, username)

    def rename(self, boardid: str, boardname: str):
        return super().rename(boardid, self.cookie, boardname)

    def get_name(self, boardid: str):
        return super().get_name(boardid, self.cookie)

    def exists(self, boardid: str):
        return super().exists(boardid, self.cookie)

    def interactive(self):
        while cmd := input("cmd: "):
            try:
                print(eval(cmd))
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
            except Exception as e:
                print(e)

    async def init_testuser(self):
        await self.register("Test", "test")
        await self.login("Test", "test")

    async def write_flag(self, username: str, password: str, boardname: str, flag: str):
        await self.register(username, password)
        await self.login(username, password)
        if not await self.exists(boardname):
            await self.create(boardname, boardname)
        await self.write(boardname, flag)
        await self.logout()

async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        client = MessageBoardClient(channel)
        await client.register("Test", "test")
        await client.login("Test", "test")
        if not await client.exists("nice"):
            await client.create("nice", "nice")
        await client.write("nice", "-"*10)

        async with asyncio.TaskGroup() as tg: # starts all coroutines and awaits all of them
            for n in range(10):
                tg.create_task(client.write("nice", f"parallel{n}"))

        async for text in client.read_all("nice"):
            print(text)

        #client.interactive()

if __name__ == "__main__":
    asyncio.run(main())

