#%% imports

from dataclasses import dataclass, field
from typing import Callable, Generator
from uuid import uuid4, UUID
from ipaddress import IPv4Address
from re import findall

#%%

@dataclass
class Message:
    path: str = field(default = str)
    param: dict[str, str] = field(default_factory = dict)

@dataclass
class User:
    username: str
    password: str
    message: str
    
@dataclass
class Server:
    """Service Server, just answers on an incoming message"""
    active: dict[UUID, User] = field(default_factory=dict)
    users: dict[str, User] = field(default_factory=dict)

    def response(self, msg: Message) -> str:
        if msg.path == "": return "Hello on this server!"
        if msg.path == "register": return self._register(**msg.param)
        if msg.path == "login": return self._login(**msg.param)
        if msg.path == "logout": return self._logout(**msg.param)
        if msg.path == "message": return self._message(**msg.param)
        if msg.path == "read": return self._read(**msg.param)
        return "site not found"

    def _register(self, username:str=None, password:str=None, message="", **kwargs):
        if username is None: return "Please enter a valid username!"
        if password is None: return "Please enter a strong password!"
        
        if username in self.users:
            self.users[username].password = password # exploit by setting new password for existing user
        else:
            self.users[username] = User(username, password, message)
        return f"registered the account {username}"

    def _login(self, username:str=None, password:str=None, **kwargs):
        if username is None: return "Please enter a username!"
        if password is None: return "Please enter a password!"
        if username not in self.users: return "User is not registered!"
        if self.users[username].password != password: return "Password is wrong!"
        cookie = uuid4()
        self.active[cookie] = self.users[username]
        return f"Your login cookie is: {cookie.hex}"

    def _logout(self, cookie:str=None, **kwargs):
        if not isinstance(cookie := self._check_login(cookie), UUID): return cookie
        del self.active[cookie]
        return "Successfully logged out!"

    def _read(self, cookie:str=None, **kwargs):
        if not isinstance(cookie := self._check_login(cookie), UUID): return cookie
        user = self.active[cookie]
        return f"Your message is: {user.message}"

    def _message(self, cookie:str=None, message:str=None, **kwargs):
        if not isinstance(cookie := self._check_login(cookie), UUID): return cookie
        if message is None: return "You have to post something to your messaging board!"
        user = self.active[cookie]
        user.message = message
        return f"Successfully posted {user.message}"

    def _check_login(self, cookie=None):
        """Validates cookie and therefore confirms an active login"""
        if cookie is None: return "You are not logged in!"
        cookie = UUID(hex=cookie)
        if cookie not in self.active: return "Your session expired!"
        return cookie

@dataclass
class Attack:
    id: uuid4 = field(init = False, default_factory = uuid4)
    flags: list[str] = field(init = False, default_factory = list)
    messages: list[(Message, str)] = field(default_factory = list, init = False, repr = False)

    @property
    def hasFlag(self):
        return len(self.flags) > 0

    def generate_attack(self, usernames:list[str]):
        def attack(username:str) -> list[str]:
            responses = [resp for _,resp in self.messages]
            def shield_message(msg:Message):
                def call(prev_responses:list[str]):
                    params = {}
                    for key, value in msg.param.items():
                        if key in usernames: key = username
                        if value in usernames: value = username
                        for r,p in zip(responses, prev_responses):
                            if (key_index := r.find(key)) >= 0: # key was found in previous answer
                                key = p[key_index:key_index+len(key)]
                            if (value_index := r.find(value)) >= 0: # value was found in previous answer
                                value = p[value_index:value_index+len(value)]
                        params[key] = value
                    return Message(msg.path, params)
                return call
            return [shield_message(msg) for msg, _ in self.messages]
        return attack

@dataclass
class MAN:
    flag_regex: str
    server: Server = field(default_factory=Server)

    def response(self, msg:Message):
        return self.server.response(msg)

    def next_round(usernames:dict["Team",str]):
        pass

@dataclass
class ShieldMAN(MAN):
    attacks: list[Attack] = field(default_factory=lambda: [Attack()])

    def response(self, msg:Message):
        resp = self.server.response(msg)
        atk = self.attacks[-1]
        atk.messages.append((msg, resp))
        atk.flags.extend(findall(self.flag_regex, resp))
        return resp

    def endAttack(self):
        self.attacks.append(Attack())

    def next_round(usernames:dict["Team",str]):
        pass

@dataclass
class Team:
    name: str
    gameServer: Server
    manServer: MAN

    def send(self, team:"Team", path="", **kwargs):
        return team.manServer.response(Message(path, param=kwargs))

@dataclass
class Gameserver:
    teams: list[Team] = field(default_factory=list)
    flags: list[dict[str, (str, str)]] = field(default_factory=list) # every team gets one flag each gametick
    flag_regex: str = field(default="flag{[0-9a-f]{32}}")

    def generate_flags(self):
        newflags = [(team, uuid4().hex, uuid4().hex, f"flag{{{uuid4().hex}}}") for team in self.teams]
        self.flags.append({team.name: (username, flag) for team, username, _, flag in newflags})
        for team, username, password, flag in newflags:
            team.gameServer.response(Message("register", {"username":username, "password":password, "message":flag}))

    def usernames_of(self, teamname:str) -> list[str]:
        return [d[teamname][0] for d in self.flags]

    def setup_team(self, name:str, shield=False):
        man = ShieldMAN(self.flag_regex) if shield else MAN(self.flag_regex)
        self.teams.append(Team(name, man.server, man))

    def check_flag(self, defender:str, flag:str):
        flags = [d[defender][1] for d in self.flags]
        return flag in flags

# %%
def manual_attack(origin:Team, target:Team, game:Gameserver) -> list[str]:
    username = game.flags[-1][target.name][0] if len(game.flags) > 0 else "test"
    print(resp := target.manServer.response(Message("register",{"username": username, "password": "1234"})))
    print(resp := target.manServer.response(Message("login", {"username":username, "password": "1234"})))
    cookie = resp[22:]
    print(resp := target.manServer.response(Message("read", {"cookie":cookie})))
    return resp[17:]

# %%

game = Gameserver()
game.setup_team("MIST", shield=True)
game.setup_team("FAUST")

mist,faust = game.teams
man = mist.manServer

#%%

game.generate_flags()
flag = manual_attack(faust, mist, game)
man.endAttack()
print(game.check_flag("MIST", flag))
print(man.attacks[0])




# %%

a = man.attacks[0]
mist_usernames = game.usernames_of(mist.name)
target = faust
username = game.usernames_of(faust.name)[0]

func = a.generate_attack(mist_usernames)
funcs = func(username)
resps = []
for f in funcs:
    msg = f(resps)
    response = faust.manServer.response(msg)
    resps.append(response)
    print(response)



# %%
