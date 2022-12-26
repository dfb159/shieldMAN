
from functools import wraps
from protos.GrpcExceptions import PermissionDenied


def wrap_owner(func):
    @wraps(func)
    def wrapper(self: "Board", owner: str, *args, **kwargs):
        if owner not in self.owner:
            raise PermissionDenied("You are not an owner of this board!")
        return func(self, *args, **kwargs)
    return wrapper
    
def wrap_reader(func):
    @wraps(func)
    def wrapper(self: "Board", reader: str, *args, **kwargs):
        if self.private and reader not in self.reader and reader not in self.owner:
            raise PermissionDenied("You cannot read this board!")
        return func(self, *args, **kwargs)
    return wrapper

class Board:
    name: str
    owner: set[str]
    reader: set[str] | None     
    messages: list[str]

    def __init__(self, name: str, creator: str, public: bool = True):
        self.name = name
        self.owner = set()
        self.owner.add(creator)
        self.reader = None if public else set()
        self.messages = []

    @property
    def public(self):
        return self.reader is None

    @property
    def private(self):
        return not self.public

    @wrap_owner
    def is_owner(self):
        pass

    @wrap_reader
    def is_reader(self):
        pass

    @wrap_owner
    def rename(self, name: str):
        self.name = name

    @wrap_owner
    def add_owner(self, new_owner: str):
        self.owner.add(new_owner)

    @wrap_owner
    def remove_owner(self, ex_owner: str):
        self.owner.discard(ex_owner)

    @wrap_owner
    def add_reader(self, new_reader: str):
        if self.private:
            self.reader.add(new_reader)

    @wrap_owner
    def remove_reader(self, ex_reader: str):
        if self.private:
            self.reader.discard(ex_reader)

    @wrap_owner
    def write(self, message: str):
        self.messages.append(message)

    @wrap_reader
    def read(self, index: int, count: int) -> list[str]:
        return self.messages[index:index+count]

    @wrap_reader
    def read_all(self) -> list[str]:
        return self.messages

    @wrap_reader
    def amount(self):
        return len(self.messages)

    @wrap_reader
    def get_name(self):
        return self.name

