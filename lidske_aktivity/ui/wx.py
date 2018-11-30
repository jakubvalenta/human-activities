import logging
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Callable, Dict, Iterable, Iterator, List, Optional

import wx
import wx.adv

from lidske_aktivity import __version__
from lidske_aktivity.store import SIZE_MODE_SIZE, SIZE_MODE_SIZE_NEW, Store

logger = logging.getLogger(__name__)


@dataclass
class RadioButtonConfig:
    name: str
    label: str
    tooltip: str


def create_sizer(parent: wx.Window,
                 orientation: int = wx.VERTICAL,
                 *args,
                 **kwargs) -> wx.BoxSizer:
    sizer = wx.BoxSizer(orientation)
    if isinstance(parent, wx.Sizer):
        parent.Add(sizer, *args, **kwargs)
    else:
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


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self,
                 on_main_menu: Callable,
                 on_about: Callable,
                 on_quit: Callable):
        super().__init__(wx.adv.TBI_DOCK)

        icon = wx.Icon()
        icon.LoadFile('/usr/share/icons/Adwaita/16x16/actions/go-home.png')
        self.SetIcon(icon)

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, on_main_menu)
        self.Bind(wx.EVT_MENU, on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, on_quit, id=wx.ID_EXIT)

    def CreatePopupMenu(self) -> wx.Menu:
        logger.warn('Create popup menu')
        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT, '&About', ' Information about this program')
        menu.Append(wx.ID_EXIT, 'E&xit', ' Terminate the program')
        return menu


class AboutBox(wx.Dialog):
    def __init__(self, parent: wx.Window):
        super().__init__()
        self.Create(parent, id=-1, title='About Lidské aktivity')
        # TODO: Icon

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = create_label(self, text='Lidské aktivity')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, '\u00a9 2018 Jakub Valena, Jiří Skála')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, 'License: GNU General Public License')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, __version__)
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, 'https://www.example.com')  # TODO
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        button_sizer = wx.StdDialogButtonSizer()
        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()
        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)


class Window(wx.PopupTransientWindow):
    store: Store
    sizer: wx.BoxSizer
    radio_buttons: List[wx.RadioButton]
    progress_bars: Dict[Path, wx.Gauge]

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
        self.border_sizer = create_sizer(self.panel)
        self.sizer = create_sizer(
            self.border_sizer,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )

    def fit(self):
        self.border_sizer.Fit(self.panel)
        self.border_sizer.Fit(self)
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
        logger.warn('ProcessLeftDown: %s' % evt.GetPosition())
        return wx.PopupTransientWindow.ProcessLeftDown(self, evt)

    def OnDismiss(self):
        logger.warn('Dismiss')


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
        self.frame = wx.Frame(parent=None, title='Foo')
        self.window = Window(store=self.store, parent=self.frame)
        self.status_icon = TaskBarIcon(
            on_main_menu=self.on_main_menu,
            on_about=self.on_menu_about,
            on_quit=self.on_menu_quit
        )
        return True

    def on_main_menu(self, event):
        logger.warn('Main menu')
        mouse_x, mouse_y = wx.GetMousePosition()
        display_id = wx.Display.GetFromWindow(self.window)
        display = wx.Display(display_id)
        _, _, screen_w, screen_h = display.GetClientArea()
        window_w, window_h = self.window.GetSize()
        window_x = min(mouse_x, max(screen_w - window_w, 0))
        window_y = min(mouse_y, max(screen_h - window_h, 0))
        logger.warn('Mouse: x=%d, y=%d', mouse_x, mouse_y)
        logger.warn('Screen: w=%d, h=%d', screen_w, screen_h)
        logger.warn('Window: w=%d, h=%d', window_w, window_h)
        logger.warn('Window: x=%d, y=%d', window_x, window_y)
        self.window.SetPosition((window_x, window_y))
        self.window.Popup()

    def on_menu_about(self, event):
        logger.warn('About')
        about = AboutBox(self.frame)
        about.ShowModal()
        about.Destroy()

    def on_menu_quit(self, event):
        logger.warn('Quit')
        self.on_quit()
        wx.CallAfter(self.frame.Close)


def run_app(store: Store, on_quit: Callable):
    app = Application(store, on_quit)
    app.MainLoop()
