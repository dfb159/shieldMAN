from math import ceil
from multiprocessing.connection import answer_challenge
from time import sleep
from typing import Generator
from uuid import uuid4
import grpc
from protos.message_board.message_board_pb2 import BoardAuth, BoardCreate, BoardReadRange, BoardText, Cookie, Credentials, PostCount
from protos.message_board.message_board_pb2_grpc import MessageBoardStub
import PySimpleGUI as sg

class MessageBoardClient:

    def __init__(self):
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = MessageBoardStub(channel)

    def register(self, username: str, password: str):
        creds = Credentials(username=username, password=password)
        self.stub.register(creds)

    def login(self, username: str, password: str) -> str:
        creds = Credentials(username=username, password=password)
        resp: Cookie = self.stub.login(creds)
        return resp.cookie

    def logout(self, cookie: str):
        cookie = Cookie(cookie=cookie)
        self.stub.logout(cookie)

    def get_count(self, boardid: str, cookie: str) -> int:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        resp: PostCount = self.stub.get_count(auth)
        return resp.count

    def read(self, boardid: str, cookie: str, index: int = 0, count: int = 1) -> Generator[str, None, None]:
        auth = BoardAuth(boardid, cookie)
        board_range = BoardReadRange(auth=auth, index=index, count=count)
        for resp in self.stub.read(board_range):
            yield resp.text

    def read_all(self, boardid: str, cookie: str) -> Generator[str, None, None]:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        for resp in self.stub.read_all(auth):
            yield resp.text

    def write(self, boardid: str, cookie: str, text: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=text)
        self.stub.write(board_text)

    def create(self, boardid: str, cookie: str, boardname: str, public: bool = True):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_create = BoardCreate(auth=auth, boardname=boardname, public=public)
        self.stub.create(board_create)

    def delete(self, boardid: str, cookie: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        self.stub.delete(auth)

    def add_owner(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        self.stub.add_owner(board_text)

    def add_reader(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        self.stub.add_reader(board_text)

    def remove_owner(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        self.stub.remove_owner(board_text)

    def remove_reader(self, boardid: str, cookie: str, username: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=username)
        self.stub.remove_reader(board_text)

    def rename(self, boardid: str, cookie: str, boardname: str):
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        board_text = BoardText(auth=auth, text=boardname)
        self.stub.rename(board_text)

    def get_name(self, boardid: str, cookie: str) -> str:
        auth = BoardAuth(boardid=boardid, cookie=cookie)
        return self.stub.get_name(auth).text

    def interactive(self):
        while cmd := input("cmd: "):
            try:
                print(eval(cmd))
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
            except Exception as e:
                print(e)

    def init_testuser(self):
        self.register("Test", "test")
        cookie = self.login("Test", "test")
        self.write(cookie, "Hello, World!")
        self.write(cookie, "FooBar")
        return cookie

class MessageBoardClientSimpleGui(MessageBoardClient):
    def __init__(self):
        super().__init__()
        self.cookie = None

        self._secret_username = "flaghunter"
        secret_password = uuid4().hex
        self._secret_flag = f"flag{{{uuid4().hex}}}"
        self.register(self._secret_username, secret_password)
        cookie = self.login(self._secret_username, secret_password)
        self.write(cookie, self._secret_flag)
        self.logout(cookie)

    def show_main(self):
        layout = [
            [sg.Text("Welcome to the ultimate Message Board!")],
            [sg.Button("Login")],
            [sg.Button("Register")],
            [sg.Button("Check Flag")],
            [sg.Cancel()],
        ]
                    
        window = sg.Window("MessageBoard Client", layout)
        event, values = window.read()
        window.close()
        
        if event == sg.WIN_CLOSED or event == "Cancel":
            return self.exit()
        if event == "Login":
            return self.show_login()
        if event == "Register":
            return self.show_register()
        if event == "Check Flag":
            return self.show_checkFlag()
        self.exit()

    def show_checkFlag(self, flag: str = ""):
        layout = [
            [sg.Text(f"Hack the following user:")],
            [sg.InputText(self._secret_username, disabled = True)],
            [sg.Text("Check your flag:")],
            [sg.InputText(flag, key='flag_input')],
            [sg.Text(key='answer')],
            [sg.Submit(), sg.Cancel()],
        ]

        window = sg.Window('Register to MessageBoard', layout)
        while True:
            event, values = window.read()
            
            if event == sg.WIN_CLOSED:
                window.close()
                return self.exit()
            if event == 'Cancel':
                window.close()
                return self.show_main()
            if event == "Submit":
                if values['flag_input'] == self._secret_flag:
                    window['answer'].update("You got it! Congrats!")
                else:
                    window['answer'].update("Sorry, not correct. Try again!")
        window.close()

    def exit(self):
        try:
            if self.cookie is not None:
                self.logout(self.cookie)
        finally:
            self.cookie = None

    def show_register(self, message: str = 'Register as a new User:', username: str = "", password: str = ""):
        layout = [
            [sg.Text(message)],
            [sg.Text("Username:"), sg.InputText(username)],
            [sg.Text("Password:"), sg.InputText(password)],
            [sg.Submit(), sg.Cancel()],
        ]

        window = sg.Window('Register to MessageBoard', layout)
        event, values = window.read()
        window.close()
        
        if event == sg.WIN_CLOSED:
            return self.exit()
        if event == 'Cancel':
            return self.show_main()
        if event == "Submit":
            username = values[0]
            password = values[1]

            try:
                self.register(username, password)
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
                return self.show_register("Could not register user! Try again:", username, password)
            except Exception as e:
                print(e)
                return self.exit()
                
            try:
                self.cookie = self.login(username, password)
                return self.show_messages()
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
                return self.show_login("User created, but could not login! Try to login manually:", username, password)
            except Exception as e:
                print(e)
                return self.exit()
        self.exit()

    def show_login(self, message: str = 'Please enter your Credentials:', username: str = "", password: str = ""):
        layout = [
            [sg.Text(message)],
            [sg.Text("Username:"), sg.InputText(username)],
            [sg.Text("Password:"), sg.InputText(password)],
            [sg.Submit(), sg.Cancel()],
        ]

        window = sg.Window('Login to MessageBoard', layout)
        event, values = window.read()
        window.close()
        
        if event == sg.WIN_CLOSED:
            return self.exit()
        if event == 'Cancel':
            return self.show_main()
        if event == "Submit":
            username = values[0]
            password = values[1]
            try:
                self.cookie = self.login(username, password)
                return self.show_messages()
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
                return self.show_login("Could not find user! Try again:", username, password)
            except Exception as e:
                print(e)
        self.exit()

    def show_messages(self, page=0, num_per_page=10):
        assert num_per_page > 0
        for _ in range(5):
            try:
                all_messages = list(self.read_all(self.cookie))
                break
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
                print("Retrying...")
                sleep(1)
            except Exception as e:
                print(e)
                return self.exit()
        else:
            print("Could not get a valid connection. Closing to main menu.")
            self.exit()
            return self.show_main()

        max_page = ceil(len(all_messages) / num_per_page)
        page = max(0, min(page, max_page-1))

        start, stop = page * num_per_page, (page+1) * num_per_page
        messages = all_messages[min(start, len(all_messages)) : min(stop,len(all_messages))]
        first_message = messages[0] if len(messages) > 0 else None

        layout = [
            [sg.Text("Your Messages:")],
            [sg.Listbox(messages, size = (40,num_per_page), no_scrollbar=True, key='messages', default_values=first_message)],
            [sg.Button("Prev", disabled=page == 0), sg.Text(f"Page {page} / {max_page}"), sg.Button("Next", disabled=page == max_page-1)],
            [sg.Button("Check Message", disabled=len(messages)==0), sg.Button("Write Message"), sg.Button("Logout")],
        ]

        window = sg.Window('Welcome to Your Messages', layout)
        event, values = window.read()
        window.close()
        
        if event == sg.WIN_CLOSED:
            return self.exit()
        if event == "Logout":
            self.exit()
            return self.show_main()
        if event == "Check Message":
            text = values['messages']
            text = text[0] if len(text) > 0 else ""
            return self.show_checkFlag(text)
        if event == "Write Message":
            return self.show_writeMessage()
        if event == "Prev":
            newpage = max(page-1, 0)
            return self.show_messages(newpage, num_per_page)
        if event == "Next":
            newpage = min(page+1, max_page-1)
            return self.show_messages(newpage, num_per_page)
        self.exit()

    def show_writeMessage(self, info: str = "Post a new Message:", message: str = ""):
        layout = [
            [sg.Text(info)],
            [sg.Multiline(message, size = (40,5), no_scrollbar=True, focus=True)],
            [sg.Submit(), sg.Cancel()],
        ]

        window = sg.Window('Write a Message', layout)
        event, values = window.read()
        window.close()
        
        if event == sg.WIN_CLOSED:
            return self.exit()
        if event == 'Cancel':
            return self.show_messages()
        if event == "Submit":
            message = values[0]
            try:
                self.write(self.cookie, message)
                self.show_messages()
            except grpc.RpcError as e:
                print(e.code())
                print(e.details())
                return self.show_writeMessage("Error while posting Message! Try again:", message)
            except Exception as e:
                print(e)
                return self.exit()
        self.exit()

    
if __name__ == "__main__":
    c = MessageBoardClientSimpleGui()
    c.show_main()
    #c.interactive()

