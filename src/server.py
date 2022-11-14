
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Message:
    path: str = field(default = str)
    param: dict[str, str] = field(default_factory = dict)
    
@dataclass
class Server:
    """Service Server, just answers an incoming message"""
    active: dict[UUID, str] = field(default_factory=dict)
    passwords: dict[str, str] = field(default_factory=dict)
    messages: dict[str, str] = field(default_factory=dict)

    def response(self, msg: Message) -> str:
        if msg.path == "": return "Hello on this server!"
        if msg.path == "register": return self._register(**msg.param)
        if msg.path == "login": return self._login(**msg.param)
        if msg.path == "logout": return self._logout(**msg.param)
        if msg.path == "message": return self._message(**msg.param)
        if msg.path == "read": return self._read(**msg.param)
        return "site not found"

    def _register(self, username:str=None, password:str=None, **kwargs):
        if username is None: return "Please enter a valid username!"
        if password is None: return "Please enter a strong password!"
        self.passwords[username] = password # exploit by setting new password for existing user
        return f"registered the account {username}"

    def _login(self, username:str=None, password:str=None, **kwargs):
        if username is None: return "Please enter a username!"
        if password is None: return "Please enter a password!"
        if username not in self.passwords: return "User is not registered!"
        if self.passwords[username] != password: return "Password is wrong!"
        cookie = uuid4()
        self.active[cookie] = username
        return f"Your login cookie is: {cookie.hex}"

    def _logout(self, cookie:str=None, **kwargs):
        if not isinstance(cookie := self._check_login(cookie), UUID): return cookie
        del self.active[cookie]
        return "Successfully logged out!"

    def _read(self, cookie:str=None, **kwargs):
        if not isinstance(cookie := self._check_login(cookie), UUID): return cookie
        user = self.active[cookie]
        return f"Your message is: {self.messages[user]}"

    def _message(self, cookie:str=None, message:str=None, **kwargs):
        if not isinstance(cookie := self._check_login(cookie), UUID): return cookie
        if message is None: return "You have to post something to your messaging board!"
        user = self.active[cookie]
        return f"Successfully posted {self.messages[user]}"

    def _check_login(self, cookie=None):
        """Validates cookie and therefore confirms an active login"""
        if cookie is None: return "You are not logged in!"
        cookie = UUID(hex=cookie)
        if cookie not in self.active: return "Your session expired!"
        return cookie
