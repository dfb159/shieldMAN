import asyncio
from uuid import uuid4
import grpc
from message_board.MessageBoardClient import MessageBoardClient
from message_board.gui.components import GUIComponent, LoginMenu, MainMenu, RegisterMenu
import PySimpleGUI as sg

class MessageBoardClientGui(MessageBoardClient):
    cookie: str | None
    window: sg.Window
    components: list[GUIComponent]
    
    def __init__(self, channel):
        super().__init__(channel)
        self.cookie = None
        self.components = [MainMenu(), LoginMenu(), RegisterMenu()]
        self.window = sg.Window("MessageBoard Client", self.layout)

    def set(self, component: str | None, *args, **kwargs):
        """Shows only the given component."""
        if component is None: return
        
        for comp in self.components:
            if comp.key==component:
                self.window[comp.key].update(visible=True)
                comp.set(self.window, *args, **kwargs)
            else:
                self.window[comp.key].update(visible=False)

    @property
    def layout(self):
        return [comp.get for comp in self.components]

    async def run(self):
        while True:
            event, values = self.window.read() # this will show the window with all oumulated updates
            print(event, values)
            
            if event == sg.WIN_CLOSED: break
            for comp in self.components:
                if event.startswith(comp.key):
                    comp(event, values, self.window, self.set)
                    break
        
        self.window.close()
        self.exit()

    def exit(self):
        try:
            if self.cookie is not None:
                self.logout(self.cookie)
        finally:
            self.cookie = None
        
async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        c = MessageBoardClientGui(channel)
        await c.write_flag("flaghunter", uuid4().hex, "flagboard", f"flag{{{uuid4().hex}}}")
        await c.run()
        #c.interactive()
    
if __name__ == "__main__":
    asyncio.run(main())
