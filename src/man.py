
from dataclasses import dataclass
from uuid import uuid4

from src.server import Message, Server


@dataclass
class MAN:
    server: Server

    def response(self, msg:Message):
        return self.server.response(msg)

    def place_flag(self, username: str, flag: str):
        self.server.passwords[username] = uuid4()
        self.server.messages[username] = flag
    
@dataclass
class Team:
    name: str
    gameServer: Server
    manServer: MAN

    def send(self, team:"Team", path="", **kwargs):
        return team.manServer.response(Message(path, param=kwargs))
