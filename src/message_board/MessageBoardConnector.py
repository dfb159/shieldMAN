from typing import Generator
from protos.message_board.message_board_pb2 import BoardAuth, BoardCreate, BoardExists, BoardReadRange, BoardText, Credentials, PostCount, Text
from protos.message_board.message_board_pb2_grpc import MessageBoardStub


class MessageBoardConnector:

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
        board_create = BoardCreate(
            auth=auth, boardname=boardname, public=public)
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
