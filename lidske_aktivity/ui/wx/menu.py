import logging
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from threading import Event, Thread
from time import sleep
from typing import Callable, Dict, Iterable, Iterator, List, Optional

import wx

from lidske_aktivity.config import save_config
from lidske_aktivity.store import SIZE_MODE_SIZE, SIZE_MODE_SIZE_NEW, Store
from lidske_aktivity.ui.wx.lib import create_button, create_label, create_sizer
from lidske_aktivity.ui.wx.setup import Setup

logger = logging.getLogger(__name__)


@dataclass
class RadioButtonConfig:
    name: str
    label: str
    tooltip: str


class Gauge(wx.Window):
    fraction: float = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, size=(-1, 5), **kwargs)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def set_fraction(self, fraction: float):
        self.fraction = fraction
        self.Refresh()

    def pulse(self):
        pass  # TODO: Add pulse support

    def on_paint(self, event):
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen('#ffffff', 1, wx.TRANSPARENT))
        w_fg = round(w * self.fraction)
        w_bg = w - w_fg
        dc.SetBrush(wx.Brush('#268bd2'))
        dc.DrawRectangle(0, 0, w_fg, h)
        dc.SetBrush(wx.Brush('#93a1a1'))
        dc.DrawRectangle(w_fg, 0, w_bg, h)


def create_progress_bar(parent: wx.Window,
                        fraction: Optional[float] = None) -> Gauge:
    progress_bar = Gauge(parent=parent)
    if fraction is not None:
        progress_bar.set_fraction(fraction)
    return progress_bar


def on_radio_update_ui(event):
    button = event.GetEventObject()
    value = button.GetValue()
    event.Enable(not value)


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


class Menu(wx.PopupTransientWindow):
    store: Store
    panel: wx.Panel
    border_sizer: wx.BoxSizer
    sizer: wx.BoxSizer
    radio_buttons: List[wx.RadioButton]
    progress_bars: Dict[Path, wx.Gauge]
    spinner: wx.StaticText
    tick_event_stop: Optional[Event] = None
    tick_thread: Optional[Thread] = None
    mouse_x: int
    mouse_y: int

    def __init__(self,
                 store: Store,
                 parent: wx.Window,
                 *args, **kwargs):
        super().__init__(*args, parent=parent, **kwargs)
        self.store = store
        self._init()

    def _init(self):
        self._init_window()
        if self.store.directories:
            self._init_radio()
            self._init_progress_bars()
            self._init_spinner()
            self._tick_start()
        else:
            self._init_empty()
        self._fit()

    def _init_window(self):
        self.panel = wx.Panel(self)
        self.border_sizer = create_sizer(self.panel)
        self.sizer = create_sizer(
            self.border_sizer,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )

    def _init_radio(self):
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
            on_toggled=self._on_radio_toggled
        ))

    def _init_empty(self):
        label = create_label(self.panel, 'No directories configured')
        self.sizer.Add(label, flag=wx.BOTTOM, border=5)
        button = create_button(
            self,
            self.panel,
            'Open app setup',
            callback=self._on_setup_button
        )
        self.sizer.Add(button, flag=wx.EXPAND)

    def _init_progress_bars(self):
        self.progress_bars = {}
        self.sizer.AddSpacer(5)
        for i, path in enumerate(self.store.directories.keys()):
            label = create_label(self, path.name)
            progress_bar = create_progress_bar(
                parent=self,
                fraction=self.store.fractions[path]
            )
            self.sizer.Add(label, flag=wx.EXPAND | wx.BOTTOM, border=3)
            self.sizer.Add(progress_bar, flag=wx.EXPAND | wx.BOTTOM, border=5)
            self.progress_bars[path] = progress_bar

    def _init_spinner(self):
        self.spinner = create_label(self, 'Processing...')
        self.sizer.Add(self.spinner, flag=wx.TOP, border=5)

    def _fit(self):
        self.border_sizer.Fit(self.panel)
        self.border_sizer.Fit(self)
        self.Layout()

    def _empty(self):
        try:
            self.panel.PopEventHandler(deleteHandler=True)
        except wx.wxAssertionError:
            pass
        self.panel.Destroy()

    def refresh(self):
        self._tick_stop()
        self._empty()
        self._init()
        self._position()

    def popup_at(self, mouse_x: int, mouse_y: int):
        self.mouse_x = mouse_x
        self.mouse_y = mouse_y
        self._position()
        self.Popup()

    def _position(self):
        display_id = wx.Display.GetFromWindow(self)
        display = wx.Display(display_id)
        _, _, screen_w, screen_h = display.GetClientArea()
        window_w, window_h = self.GetSize()
        SCREEN_MARGIN = 10
        window_x = min(
            self.mouse_x,
            max(screen_w - window_w - SCREEN_MARGIN, SCREEN_MARGIN)
        )
        window_y = min(
            self.mouse_y,
            max(screen_h - window_h - SCREEN_MARGIN, SCREEN_MARGIN)
        )
        self.SetPosition((window_x, window_y))

    def _on_radio_toggled(self, event, button: wx.ToggleButton, mode: str):
        self.store.set_active_mode(mode)
        for other_button in self.radio_buttons:
            if other_button != button:
                other_button.SetValue(False)
        self._on_tick(pulse=False)

    def _tick_start(self):
        self.tick_event_stop = Event()
        self.tick_thread = Thread(target=self._tick)
        self.tick_thread.start()

    def _tick_stop(self):
        if self.tick_event_stop is not None:
            self.tick_event_stop.set()
        if self.tick_thread is not None:
            self.tick_thread.join()
        logger.info('Tick stopped')

    def _tick(self):
        while not self.tick_event_stop.is_set():
            wx.CallAfter(self._on_tick)
            sleep(1)

    def _on_tick(self, pulse: bool = True):
        logger.info('Updating progress bars')
        if self.store.directories:
            for path, d in self.store.directories.items():
                if d.size is None:
                    if pulse:
                        self.progress_bars[path].pulse()
                else:
                    self.progress_bars[path].set_fraction(
                        self.store.fractions[path]
                    )
        if not any(self.store.pending.values()):
            self.spinner.Hide()
            self._fit()

    def _on_setup_button(self, event):
        self.Hide()
        setup = Setup(self, self.store.config)
        val = setup.ShowModal()
        if val == wx.ID_OK:
            self.store.config = setup.config
            self.refresh()
            save_config(self.store.config)
        self.Show()

    def ProcessLeftDown(self, event):
        logger.info('ProcessLeftDown: %s' % event.GetPosition())
        return wx.PopupTransientWindow.ProcessLeftDown(self, event)

    def OnExit(self):
        self._tick_stop()
        super().OnExit()
        return True
