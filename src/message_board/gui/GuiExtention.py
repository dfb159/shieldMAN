import PySimpleGUI as sg

from message_board.MessageBoardClient import MessageBoardClient


class GuiComponent:
    key: str

    @property
    def layout(self):
        raise NotImplementedError()

    async def set(self, window: sg.Window):
        pass

    async def __call__(self, event, values, window: sg.Window, client: MessageBoardClient):
        pass


class PinComponent(GuiComponent):
    visible: bool = False

    @property
    def pin(self):
        return sg.pin(sg.Column(self.layout, key=self.key, visible=self.visible))

    async def __call__(self, event, values, window: sg.Window, set_comp, client: MessageBoardClient):
        pass


class PinGroupComponent:
    components: list[PinComponent]

    def __init__(self, *components: PinComponent):
        self.components = list(components)

    @property
    def layout(self):
        return [[comp.pin] for comp in self.components]

    async def set(self, window: sg.Window, component: str, *args, **kwargs):
        """Shows only the given component."""
        for comp in self.components:
            if comp.key == component:
                window[comp.key].update(visible=True)
                await comp.set(window, *args, **kwargs)
            else:
                window[comp.key].update(visible=False)

    async def __call__(self, event, values, window: sg.Window, client: MessageBoardClient):
        def inner_set(component: str, *args, **kwargs):
            return self.set(window, component, *args, **kwargs)
        for comp in self.components:
            if event.startswith(comp.key):
                await comp(event, values, window, inner_set, client)


class TabComponent(GuiComponent):
    name: str = "TabComponent"

    @property
    def tab(self):
        return sg.Tab(self.name, self.layout, key=self.key)

    async def __call__(self, event, values, window: sg.Window, add_tab, client: MessageBoardClient):
        pass


class TabGroupComponent(GuiComponent):
    tabs: list[TabComponent]

    def __init__(self, key, *tabs: TabComponent):
        self.key = key
        self.tabs = list(tabs)

    @property
    def layout(self):
        return sg.TabGroup([[tab.tab for tab in self.tabs]], key=self.key)

    async def __call__(self, event: str, values, window: sg.Window, client: MessageBoardClient):
        added: list[tuple[TabComponent, bool]] = []
        def inner_add(tab: TabComponent, select=False):
            for t in self.tabs:
                if tab.key == t.key: return
            added.append((tab, select))
        tabGroup: sg.TabGroup = window[self.key]
        for comp in self.tabs:
            if event.startswith(comp.key) or comp.key == tabGroup.get():
                await comp(event, values, window, inner_add, client)
        for tab, select in added:
            self.tabs.append(tab)
            window[self.key].add_tab(tab.tab)
            if select:
                window[tab.key].select()
            await tab(event, values, window, inner_add, client)
