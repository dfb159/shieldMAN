
from dataclasses import dataclass, field
from uuid import uuid4

from src.man import Team


@dataclass
class Gameserver:
    teams: dict[str, Team] = field(default_factory=dict)
    flags: list[dict[(str, str), (str, str)]] = field(default_factory=list) # each gametick one flag is generated for every Team:Team pair
    flag_regex: str = field(default="flag{[0-9a-f]{32}}")

    def generate_flags(self):
        newflags = {(atk, dev): (uuid4().hex, f"flag{{{uuid4().hex}}}") for atk in self.teams for dev in self.teams}
        for (_, dev), (username, flag) in newflags.items():
            self.teams[dev].manServer.place_flag(username, flag)
        self.flags.append(newflags)

    def add_team(self, team: Team):
        self.teams[team.name] = team
        
    def usernames(self, attacker: Team, defender: Team, index: int = None) -> list[str]:
        name = lambda d: d[(attacker.name, defender.name)][0]
        return [name(d) for d in self.flags] if index is None else name(self.flags[index])

    def check_flag(self, attacker: Team, defender: Team, flag: str) -> bool:
        flags = [d[(attacker.name,defender.name)][1] for d in self.flags]
        return flag in flags