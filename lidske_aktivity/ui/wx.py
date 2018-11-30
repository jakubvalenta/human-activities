import logging
from dataclasses import dataclass
from functools import partial
from threading import Event, Thread
from time import sleep
from typing import Callable, Dict, Iterable, Iterator, List, Optional

import wx
import wx.adv

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


def on_radio_update_ui(event):
    button = event.GetEventObject()
    value = button.GetValue()
    event.Enable(not value)


def create_label(parent: wx.Window, text: str) -> wx.StaticText:
    return wx.StaticText(parent, label=text)


def create_progress_bar(parent: wx.Window,
                        fraction: Optional[float] = None) -> wx.Gauge:
    progress_bar = wx.Gauge(parent=parent, range=100)
    if fraction is not None:
        progress_bar.SetValue(round(fraction * 100))
    # progress_bar.set_pulse_step(1)
    return progress_bar


def create_radio_buttons(window: wx.Window,
                         parent: wx.Window,
                         configs: Iterable[RadioButtonConfig],
                         active_name: str,
                         on_toggled: Callable) -> Iterator[wx.ToggleButton]:
    grid = wx.GridSizer(cols=2)
    for config in configs:
        button = wx.ToggleButton(
            parent=window,
            label=config.label,
        )
        button.SetValue(config.name == active_name)
        button.Bind(
            wx.EVT_TOGGLEBUTTON,
            partial(on_toggled, button=button, mode=config.name)
        )
        button.Bind(
            wx.EVT_UPDATE_UI,
            on_radio_update_ui,
        )
        grid.Add(button)
        yield button
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


class TaskBarIcon(wx.adv.TaskBarIcon):

    def __init__(self,
                 parent: wx.Window,
                 on_about: Callable,
                 on_quit: Callable):
        super().__init__()
        self.parent = parent
        self.on_about = on_about
        self.on_quit = on_quit

    def CreatePopupMenu(self) -> wx.Menu:
        logger.warn('Create popup menu')
        return create_context_menu(self.parent, self.on_about, self.on_quit)


def create_status_icon(parent: wx.Window,
                       on_main_menu: Callable,
                       on_about: Callable,
                       on_quit: Callable) -> wx.adv.TaskBarIcon:
    icon = wx.Icon()
    icon.LoadFile('/usr/share/icons/Adwaita/16x16/actions/go-home.png')
    status_icon = TaskBarIcon(parent, on_about, on_quit)
    status_icon.SetIcon(icon)
    status_icon.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, on_main_menu)
    return status_icon


def show_about_dialog():
    wx.MessageBox(
        'This is a wxPython Hello World sample About Hello World 2',
        wx.OK | wx.ICON_INFORMATION
    )


class Window(wx.PopupTransientWindow):
    store: Store
    sizer: wx.BoxSizer
    radio_buttons: List[wx.RadioButton]
    progress_bars: Dict[str, wx.Gauge]

    def __init__(self,
                 store: Store,
                 parent: wx.Window,
                 *args, **kwargs):
        super().__init__(*args, parent=parent, **kwargs)
        self.store = store
        self.init_window()
        self.init_radio()
        self.init_progress_bars()
        self.init_spinner()
        self.tick_start()
        self.fit()
        logger.warn('Done')

    def init_window(self):
        self.panel = wx.Panel(self)
        self.sizer = create_sizer(self, wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

    def fit(self):
        self.sizer.Fit(self.panel)
        self.sizer.Fit(self)
        self.Layout()

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
        self.radio_buttons = list(create_radio_buttons(
            window=self,
            parent=self.sizer,
            configs=radio_button_configs,
            active_name=self.store.active_mode,
            on_toggled=self.on_radio_toggled
        ))

    def init_progress_bars(self):
        self.progress_bars = {}
        if not self.store.directories:
            label = create_label(self, 'No directories found')
            self.sizer.Add(label)
            return
        for path, d in self.store.directories.items():
            label = create_label(self, path.name)
            progress_bar = create_progress_bar(
                parent=self,
                fraction=self.store.fractions[path]
            )
            self.sizer.Add(label)
            self.sizer.Add(progress_bar)
            self.progress_bars[path] = progress_bar

    def init_spinner(self):
        self.size_remember()
        self.spinner = create_label(self, 'Processing...')
        self.sizer.Add(self.spinner)

    def on_radio_toggled(self, event, button: wx.ToggleButton, mode: str):
        logger.warn('Toogled %s = %s', button, mode)
        self.store.set_active_mode(mode)
        for other_button in self.radio_buttons:
            if other_button != button:
                other_button.SetValue(False)
        self.on_tick(pulse=False)

    def tick_start(self):
        self.tick_event_stop = Event()
        self.tick_thread = Thread(target=self.tick)
        self.tick_thread.start()

    def tick_stop(self):
        self.tick_event_stop.set()
        self.tick_thread.join()
        logger.info('Tick stopped')

    def tick(self):
        while not self.tick_event_stop.is_set():
            self.on_tick()
            sleep(1)

    def on_tick(self, pulse: bool = True):
        logger.info('Updating progress bars')
        if self.store.directories:
            for path, d in self.store.directories.items():
                if d.size is None:
                    if pulse:
                        self.progress_bars[path].Pulse()
                else:
                    self.progress_bars[path].SetValue(
                        round(self.store.fractions[path] * 100)
                    )
        if not any(self.store.pending.values()):
            self.spinner.Hide()
            self.size_restore()

    def size_remember(self):
        pass
        # self.size = self.get_size()  # TODO

    def size_restore(self):
        pass
        # self.resize(*self.size)  # TODO

    def ProcessLeftDown(self, evt):
        logger.warn("ProcessLeftDown: %s\n" % evt.GetPosition())
        return wx.PopupTransientWindow.ProcessLeftDown(self, evt)

    def OnDismiss(self):
        logger.warn("OnDismiss\n")


class Application(wx.App):
    window: Window
    store: Store
    on_quit: Callable
    status_icon: wx.adv.TaskBarIcon

    def __init__(self, store: Store, on_quit: Callable, *args, **kwargs):
        self.store = store
        self.on_quit = on_quit
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        parent = wx.Frame(parent=None, title='Foo')
        self.window = Window(store=self.store, parent=parent)
        self.status_icon = create_status_icon(
            parent=parent,
            on_main_menu=self.on_main_menu,
            on_about=self.on_menu_about,
            on_quit=self.on_menu_quit
        )
        return True

    def on_main_menu(self, event):
        logger.warn('Main menu')
        # status_icon = event.GetEventObject()
        # import ipdb; ipdb.set_trace()
        # position = status_icon.ClientToScreen((0, 0))
        # logger.warn('Position: %s x %s', *position)
        self.window.Show(True)

    def on_menu_about(self, event):
        logger.warn('About')
        show_about_dialog()

    def on_menu_quit(self, event, on_quit):
        logger.warn('Quit')
        on_quit()
        self.window.Close(True)


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.MainLoop()
