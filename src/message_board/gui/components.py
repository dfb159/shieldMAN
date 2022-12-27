import PySimpleGUI as sg
import grpc

from message_board.MessageBoardClient import MessageBoardClient

class GUIComponent:
    key: str = "-BaseComponent-"
    visible: bool = False
        
    @property
    def layout(self):
        raise NotImplementedError()

    @property
    def get(self):
        return [sg.pin(sg.Column(self.layout, key=self.key, visible=self.visible))]

    async def set(self, window: sg.Window):
        pass

    async def __call__(self, event, values, window: sg.Window, set_comp, client: MessageBoardClient):
        """Passes the event to this Component."""
        raise NotImplementedError()

class MainMenu(GUIComponent):
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
        if event == MainMenu.login_key: await set_comp(LoginMenu.key)
        if event == MainMenu.register_key: await set_comp(RegisterMenu.key)

class LoginMenu(GUIComponent):
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
            [sg.Button("Login", key=LoginMenu.login_key), sg.Button("Register", key=LoginMenu.register_key), sg.Button("Cancel", key=LoginMenu.cancel_key)],
        ]
    
    async def set(self, window: sg.Window, message = default_message, username="", password=""):
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
    
class RegisterMenu(GUIComponent):
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
            [sg.Text(RegisterMenu.default_message, key=RegisterMenu.message_key)],
            [sg.Text("Username:"), sg.InputText(key=RegisterMenu.username_key)],
            [sg.Text("Password:"), sg.InputText(key=RegisterMenu.password_key)],
            [sg.Button("Register", key=RegisterMenu.register_key), sg.Button("Login", key=RegisterMenu.login_key), sg.Button("Cancel", key=RegisterMenu.cancel_key)],
        ]

    async def set(self, window: sg.Window, message = default_message, username = "", password = ""):
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

class BoardMenu(GUIComponent):
    key: str = "-board-"
    message_key = f"{key}message-"
    logout_key = f"{key}logout-"

    default_message = "Welcome to your account"

    @property
    def layout(self):
        
        return [
            [sg.Text(BoardMenu.default_message, key=BoardMenu.message_key)],
            [sg.Button("Logout", key=BoardMenu.logout_key)],
        ]

    async def set(self, window: sg.Window, message = default_message):
        window[BoardMenu.message_key].update(value=message)

    async def __call__(self, event, values, window: sg.Window, set_comp, client: MessageBoardClient):
        if event == BoardMenu.logout_key:
            await set_comp(MainMenu.key)
