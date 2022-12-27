import asyncio
from uuid import uuid4
import grpc
from message_board.MessageBoardClient import MessageBoardClient
from message_board.gui.components import BoardMenu, GUIComponent, LoginMenu, MainMenu, RegisterMenu
import PySimpleGUI as sg

class MessageBoardClientGui:
    client: MessageBoardClient
    window: sg.Window
    components: list[GUIComponent]
    
    def __init__(self, channel):
        self.client = MessageBoardClient(channel)
        self.components = [MainMenu(), LoginMenu(), RegisterMenu(), BoardMenu()]
        self.window = sg.Window("MessageBoard Client", self.layout)

    async def set(self, component: str | None, *args, **kwargs):
        """Shows only the given component."""
        if component is None: return
        
        for comp in self.components:
            if comp.key==component:
                self.window[comp.key].update(visible=True)
                await comp.set(self.window, *args, **kwargs)
            else:
                self.window[comp.key].update(visible=False)

    @property
    def layout(self):
        return [comp.get for comp in self.components]

    async def run(self):
        while True:
            event, values = self.window.read() # this will show the window with all oumulated updates
            
            if event == sg.WIN_CLOSED: break
            for comp in self.components:
                if event.startswith(comp.key):
                    await comp(event, values, self.window, self.set, self.client)
                    break
        
        self.window.close()
        
async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        gui = MessageBoardClientGui(channel)
        await gui.client.write_flag("flaghunter", uuid4().hex, "flagboard", f"flag{{{uuid4().hex}}}")
        await gui.run()
        #c.interactive()
    
if __name__ == "__main__":
    asyncio.run(main())
