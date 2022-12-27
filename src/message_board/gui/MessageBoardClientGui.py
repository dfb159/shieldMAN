import asyncio
from uuid import uuid4
import grpc
from message_board.MessageBoardClient import MessageBoardClient
from message_board.gui.GuiExtention import PinGroupComponent
from message_board.gui.components import BoardMenu, LoginMenu, MainMenu, PinComponent, RegisterMenu
import PySimpleGUI as sg


class MessageBoardClientGui:
    client: MessageBoardClient
    window: sg.Window
    pin_group: PinGroupComponent

    def __init__(self, channel):
        self.client = MessageBoardClient(channel)
        self.pin_group = PinGroupComponent(
            MainMenu(), LoginMenu(), RegisterMenu(), BoardMenu())
        self.window = sg.Window("MessageBoard Client", self.pin_group.layout)

    async def run(self):
        while True:
            # this will show the window with all cumulated updates
            event, values = self.window.read(timeout=1000)
            # print(event, values)

            if event == sg.WIN_CLOSED:
                break
            # if event == sg.EVENT_TIMEOUT: print("timeout")
            await self.pin_group(event, values, self.window, self.client)

        self.window.close()
        self.client.logout()


async def main():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        gui = MessageBoardClientGui(channel)
        await gui.client.write_flag("flaghunter", uuid4().hex, "flagboard", f"flag{{{uuid4().hex}}}")
        await gui.run()
        # c.interactive()

if __name__ == "__main__":
    asyncio.run(main())
