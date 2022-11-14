from src.game import Gameserver

from src.server import Server, Message
from src.man import MAN, Team
from src.shield import ShieldMAN

def manual_attack(attacker: Team, defender: Team, game: Gameserver, index: int = -1) -> list[str]:
    username = game.usernames(attacker, defender, index)
    print(resp := defender.manServer.response(Message("register",{"username": username, "password": "1234"})))
    print(resp := defender.manServer.response(Message("login", {"username":username, "password": "1234"})))
    cookie = resp[22:]
    print(resp := defender.manServer.response(Message("read", {"cookie":cookie})))
    return resp[17:]

# Setup game server and teams
game = Gameserver()
game.add_team(mist := Team("MIST", mistServer := Server(),  mistMan := ShieldMAN(flag_regex = game.flag_regex, server = mistServer)))
game.add_team(faust := Team("FAUST", faustServer := Server(), faustMan := MAN(server = faustServer)))

# First Game round: faust attacked mist 
game.generate_flags()
flag = manual_attack(faust, mist, game)
print("Flag was correct:", game.check_flag(faust, mist, flag))

# mist extracted shield attack
a = mistMan.attacks[0]
mist_usernames = game.usernames(faust, mist)
username = game.usernames(mist, faust, 0)

func = a.generate_attack(mist_usernames)
funcs = func(username)
resps = []
for f in funcs:
    msg = f(resps)
    response = faust.manServer.response(msg)
    resps.append(response)
    print(response)

print("\ngenerated attack script:\n")

print(a.generate_script(mist_usernames))
