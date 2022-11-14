
from dataclasses import dataclass, field
from re import findall
from uuid import uuid4

from src.man import MAN, Team
from src.server import Message, Server


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
    
    def generate_script(self, usernames:list[str]) -> str:
        script = "def attack(team: Team, username: str) -> list[str]:\n"
        script += "    resps = []\n"
        msgs, resps = zip(*self.messages)

        for i,msg in enumerate(msgs):
            params = []
            for key, value in msg.param.items():
                keystr, valuestr = f"\"{key}\"", f"\"{value}\""
                if key in usernames: keystr = "username"
                if value in usernames: valuestr = "username"
                for j,r in enumerate(resps[:i]):
                    if (key_index := r.find(key)) >= 0: # key was found in previous answer
                        keystr = f"resps[{j}][{key_index}:{key_index+len(key)}]"
                    if (value_index := r.find(value)) >= 0: # value was found in previous answer
                        valuestr = f"resps[{j}][{value_index}:{value_index+len(key)}]"
                params.append(f"{keystr}: {valuestr}")
            params = f"{{{', '.join(params)}}}"
            script += f"    resps.append(team.manServer.response(Message(path='{msg.path}', param={params})))\n"
        return script
 
class ShieldMAN(MAN):

    def __init__(self, flag_regex: str, server: Server = None):
        super().__init__(server = server)
        self.flag_regex = flag_regex
        self.attacks = [Attack()]

    def response(self, msg:Message):
        resp = self.server.response(msg)
        atk = self.attacks[-1]
        atk.messages.append((msg, resp))
        atk.flags.extend(findall(self.flag_regex, resp))
        return resp

    def end_attack(self):
        self.attacks.append(Attack())
