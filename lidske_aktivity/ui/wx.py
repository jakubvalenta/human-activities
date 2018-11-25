import logging
from dataclasses import dataclass
from typing import Callable, Iterable

import wx

from lidske_aktivity.store import SIZE_MODE_SIZE, SIZE_MODE_SIZE_NEW, Store

logger = logging.getLogger(__name__)


@dataclass
class RadioButtonConfig:
    name: str
    label: str
    tooltip: str


def create_sizer(parent: wx.Window, orientation) -> wx.BoxSizer:
    sizer = wx.BoxSizer(orientation)
    parent.SetSizer(sizer)
    parent.SetAutoLayout(1)
    sizer.Fit(parent)
    return sizer


def create_radio_buttons(window: wx.Window,
                         parent: wx.Window,
                         configs: Iterable[RadioButtonConfig],
                         active_name: str,
                         on_toggled: Callable):
    grid = wx.GridSizer(cols=2)
    for config in configs:
        button = wx.ToggleButton(parent=window, label=config.label)
        button.SetValue(config.name == active_name)
        button.Bind(wx.EVT_TOGGLEBUTTON, lambda event: on_toggled(config.name))
        grid.Add(button)
    parent.Add(grid)


def create_menu_item(menu: wx.Menu,
                     frame: wx.Frame,
                     id_: str,
                     label: str,
                     tooltip: str,
                     callback: Callable = None):
    menu_item = menu.Append(id_, label, tooltip)
    if callback:
        frame.Bind(wx.EVT_MENU, callback, menu_item)


def create_context_menu(frame: wx.Frame,
                        on_about: Callable,
                        on_quit: Callable) -> wx.Menu:
    context_menu = wx.Menu()
    create_menu_item(
        menu=context_menu,
        frame=frame,
        id_=wx.ID_ABOUT,
        label='&About',
        tooltip=' Information about this program',
        callback=on_about
    )
    create_menu_item(
        menu=context_menu,
        frame=frame,
        id_=wx.ID_EXIT,
        label='E&xit',
        tooltip=' Terminate the program',
        callback=on_about
    )
    return context_menu


def show_about_dialog():
    wx.MessageBox(
        'This is a wxPython Hello World sample About Hello World 2',
        wx.OK | wx.ICON_INFORMATION
    )


class Frame(wx.Frame):
    store: Store
    on_quit: Callable

    sizer: wx.BoxSizer

    def __init__(self, store: Store, on_quit: Callable, *args, **kwargs):
        super().__init__(*args, parent=None, title='Lidské aktivity', **kwargs)
        self.store = store
        self.on_quit = on_quit
        self.context_menu = create_context_menu(
            frame=self,
            on_about=self.on_menu_about,
            on_quit=self.on_menu_quit
        )
        self.init_window()
        self.init_radio()
        self.init_progress_bars()
        self.init_spinner()
        self.tick_start()

    def init_window(self):
        self.sizer = create_sizer(self, wx.VERTICAL)
        self.Show()

    def init_radio(self):
        radio_button_configs = [
            RadioButtonConfig(
                name=SIZE_MODE_SIZE,
                label='by size',
                tooltip=(
                    'Each bar shows the fraction of the total root directory '
                    'size that the given directory occupies.'
                )
            ),
            RadioButtonConfig(
                name=SIZE_MODE_SIZE_NEW,
                label='by activity',
                tooltip=(
                    'Each bar shows the fraction of the size of the given '
                    'directory that was modified in the last 30 days.'
                )
            ),
        ]
        radio_buttons = create_radio_buttons(
            window=self,
            parent=self.sizer,
            configs=radio_button_configs,
            active_name=self.store.active_mode,
            on_toggled=self.on_radio_toggled
        )

    def init_progress_bars(self):
        pass

    def init_spinner(self):
        pass

    def tick_start(self):
        pass

    def on_radio_toggled(self, mode: str):
        self.store.set_active_mode(mode)

    def on_menu_about(self, event):
        show_about_dialog()

    def on_menu_quit(self, event):
        self.on_quit()
        self.Close(True)


def run_app(store: Store, on_quit: Callable):
    app = wx.App()
    frame = Frame(store, on_quit)
    frame.Show()
    app.MainLoop()
