from math import ceil
import PySimpleGUI as sg
import pyperclip

from message_board.MessageBoardClient import MessageBoardClient
from message_board.gui.GuiExtention import PinComponent, TabComponent, TabGroupComponent


class MainMenu(PinComponent):
    key: str = "-main-"
    visible: bool = True
    login_key = f"{key}login-"
    register_key = f"{key}register-"

    @property
    def layout(self):
        return [
            [sg.Text("Welcome to the ultimate Message Board!")],
            [sg.Button("Login", key=MainMenu.login_key)],
            [sg.Button("Register", key=MainMenu.register_key)],
        ]

    async def __call__(self, event, values, window: sg.Window, set_comp, client: MessageBoardClient):
        if event == MainMenu.login_key:
            await set_comp(LoginMenu.key)
        if event == MainMenu.register_key:
            await set_comp(RegisterMenu.key)


class LoginMenu(PinComponent):
    key: str = "-login-"
    message_key = f"{key}message-"
    username_key = f"{key}username-"
    password_key = f"{key}password-"
    login_key = f"{key}login-"
    register_key = f"{key}register-"
    cancel_key = f"{key}cancel-"

    default_message = "Enter your credentials to login:"

    @property
    def layout(self):

        return [
            [sg.Text(LoginMenu.default_message, key=LoginMenu.message_key)],
            [sg.Text("Username:"), sg.InputText(key=LoginMenu.username_key)],
            [sg.Text("Password:"), sg.InputText(key=LoginMenu.password_key)],
            [sg.Button("Login", key=LoginMenu.login_key), sg.Button(
                "Register", key=LoginMenu.register_key), sg.Button("Cancel", key=LoginMenu.cancel_key)],
        ]

    async def set(self, window: sg.Window, message=default_message, username="", password=""):
        window[LoginMenu.message_key].update(value=message)
        window[LoginMenu.username_key].update(value=username)
        window[LoginMenu.password_key].update(value=password)

    async def login(self, username: str, password: str, set_comp, client: MessageBoardClient):
        try:
            await client.login(username, password)
        except:
            await set_comp(LoginMenu.key, message="Login failed. Try again!", username=username, password=password)
        else:
            await set_comp(BoardMenu.key)

    async def __call__(self, event, values, window: sg.Window, set_comp, client: MessageBoardClient):
        username = values[LoginMenu.username_key]
        password = values[LoginMenu.password_key]
        if event == LoginMenu.login_key:
            await self.login(username, password, set_comp, client)
        if event == LoginMenu.register_key:
            await set_comp(RegisterMenu.key, username=username, password=password)
        if event == LoginMenu.cancel_key:
            await set_comp(MainMenu.key)


class RegisterMenu(PinComponent):
    key: str = "-register-"
    message_key = f"{key}message-"
    username_key = f"{key}username-"
    password_key = f"{key}password-"
    login_key = f"{key}login-"
    register_key = f"{key}register-"
    cancel_key = f"{key}cancel-"

    default_message = "Enter your credentials create a new account:"

    @property
    def layout(self):

        return [
            [sg.Text(RegisterMenu.default_message,
                     key=RegisterMenu.message_key)],
            [sg.Text("Username:"), sg.InputText(
                key=RegisterMenu.username_key)],
            [sg.Text("Password:"), sg.InputText(
                key=RegisterMenu.password_key)],
            [sg.Button("Register", key=RegisterMenu.register_key), sg.Button(
                "Login", key=RegisterMenu.login_key), sg.Button("Cancel", key=RegisterMenu.cancel_key)],
        ]

    async def set(self, window: sg.Window, message=default_message, username="", password=""):
        window[RegisterMenu.message_key].update(value=message)
        window[RegisterMenu.username_key].update(value=username)
        window[RegisterMenu.password_key].update(value=password)

    async def register(self, username: str, password: str, set_comp, client: MessageBoardClient):
        try:
            await client.register(username, password)
        except:
            await set_comp(RegisterMenu.key, message="Register failed. Try again!", username=username, password=password)
            return

        try:
            await client.login(username, password)
        except:
            await set_comp(LoginMenu.key, message="Login failed. Try manually!", username=username, password=password)
            return

        await set_comp(BoardMenu.key)

    async def __call__(self, event, values, window: sg.Window, set_comp, client: MessageBoardClient):
        username = values[RegisterMenu.username_key]
        password = values[RegisterMenu.password_key]

        if event == RegisterMenu.register_key:
            await self.register(username, password, set_comp, client)
        if event == RegisterMenu.login_key:
            await set_comp(LoginMenu.key, username=username, password=password)
        if event == RegisterMenu.cancel_key:
            await set_comp(MainMenu.key)


class BoardTabNew(TabComponent):
    name = "Add Board"
    key = "-board-new-"
    add_key = f"{key}add-"
    id_key = f"{key}id-"
    name_key = f"{key}name-"
    public_key = f"{key}public-"

    @property
    def layout(self):
        return [
            [sg.Text("Boardid:"), sg.InputText(key=BoardTabNew.id_key)],
            [sg.Text("Boardname:"), sg.InputText(key=BoardTabNew.name_key)],
            [sg.Checkbox("public", default=True, key=BoardTabNew.public_key)],
            [sg.Button("Add board", key=BoardTabNew.add_key)],
        ]

    async def __call__(self, event, values, window: sg.Window, add_tab, client: MessageBoardClient):
        if event == BoardTabNew.add_key:
            id = values[BoardTabNew.id_key]
            name = values[BoardTabNew.name_key]
            public = values[BoardTabNew.public_key]
            key = f"{BoardMenu.key}{id}-"
            try:
                if not await client.exists(id):
                    await client.create(id, name, public)
                tab = BoardTab(key, id, name)
                add_tab(tab, True)
                window[BoardTabNew.id_key].update("")
                window[BoardTabNew.name_key].update("")
                window[BoardTabNew.public_key].update(True)
            except:
                pass


class BoardTab(TabComponent):
    boardid: str
    messages: list[str]
    num_per_page: int = 15
    page: int

    def __init__(self, key: str, boardid: str, boardname: str):
        super().__init__()
        self.boardid = boardid
        self.name = boardname
        self.messages = []
        self.page = 0
        self.key = key
        self.name_key = f"{self.key}name-"
        self.status_key = f"{self.key}status-"
        self.rename_key = f"{self.key}rename-"
        self.messages_key = f"{self.key}messages-"
        self.text_key = f"{self.key}text-"
        self.write_key = f"{self.key}write-"
        self.prev_key = f"{self.key}prev-"
        self.page_key = f"{self.key}page-"
        self.next_key = f"{self.key}next-"
        self.copy_key = f"{self.key}copy-"

    @property
    def layout(self):
        return [
            [sg.Text("Boardname:"), sg.InputText(self.name, size=(20,1), key=self.name_key), sg.Button("Rename", key=self.rename_key)],
            # [sg.Text("---", key=self.status_key)],  # Cant read, no owner, ...
            [sg.Listbox(self.messages, size=(40, self.num_per_page), no_scrollbar=True, key=self.messages_key)],
            [sg.Button("Prev", key=self.prev_key), sg.Text("0 / 0", key=self.page_key), sg.Button("Next", key=self.next_key)],
            [sg.InputText(key=self.text_key), sg.Button("Write", key=self.write_key), sg.Button("Copy", key=self.copy_key)],
        ]

    async def __call__(self, event, values, window: sg.Window, add_tab, client: MessageBoardClient):
        if event == self.rename_key:
            name = values[self.name_key]
            await client.rename(self.boardid, name)
        if event == self.write_key:
            text = values[self.text_key]
            await client.write(self.boardid, text)
            window[self.text_key].update("")
        if event == self.prev_key:
            self.page -= 1
        if event == self.next_key:
            self.page += 1
        if event == self.copy_key:
            text = window[self.messages_key].get()
            if len(text) > 0:
                pyperclip.copy(text[0])
            
        count = await client.get_count(self.boardid)
        lenpage = ceil(count / self.num_per_page)
        self.page = max(0, min(self.page, lenpage-1))
        window[self.page_key].update(f"{self.page+1} / {lenpage}") # shows 1 / 0 for empty board

        try:
            self.name = await client.get_name(self.boardid)
            self.messages = [text async for text in client.read(self.boardid, self.page*self.num_per_page, self.num_per_page)]
        except:
            self.name = "private"
            self.messages = []

        window[self.key].update(title=self.name)
        window[self.name_key].update(value=self.name)
        window[self.messages_key].update(self.messages)


class BoardTabs(TabGroupComponent):
    def __init__(self, *tabs: TabComponent):
        super().__init__("-board-tabs-", BoardTabNew())

    async def __call__(self, event, values, window: sg.Window, client: MessageBoardClient):
        super().__call__(event, values, window, client)


class BoardMenu(PinComponent):
    key: str = "-board-"
    boards_key = f"{key}tabs-"
    message_key = f"{key}message-"
    logout_key = f"{key}logout-"

    default_message = "Welcome to your account"

    boards: TabGroupComponent

    def __init__(self):
        self.boards = TabGroupComponent(BoardMenu.boards_key, BoardTabNew())

    @property
    def layout(self):
        return [
            [sg.Text(BoardMenu.default_message, key=BoardMenu.message_key)],
            [self.boards.layout],
            [sg.Button("Logout", key=BoardMenu.logout_key)],
        ]

    async def set(self, window: sg.Window, message=default_message):
        window[BoardMenu.message_key].update(value=message)

    async def __call__(self, event, values, window: sg.Window, set_comp, client: MessageBoardClient):
        if event == BoardMenu.logout_key:
            await set_comp(MainMenu.key)
        await self.boards(event, values, window, client)
