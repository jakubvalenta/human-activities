import logging
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional

import wx

from lidske_aktivity.bitmap import TColor, color_from_index
from lidske_aktivity.config import MODE_NAMED, save_config
from lidske_aktivity.store import (
    SIZE_MODE_SIZE, SIZE_MODE_SIZE_NEW, Store, TFractions,
)
from lidske_aktivity.ui.lib import (
    create_button, create_label, create_sizer, set_pen,
)
from lidske_aktivity.ui.setup import Setup

logger = logging.getLogger(__name__)


class Gauge(wx.Window):
    color: TColor
    fraction: float = 0
    is_pulse: bool = True
    default_color: TColor = (147, 161, 161, 255)

    def __init__(self, parent: wx.Window, color: TColor):
        self.color = color
        super().__init__(parent, size=(-1, 5))
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def set_fraction(self, fraction: float):
        self.is_pulse = False
        self.fraction = fraction
        self.Refresh()

    def pulse(self):
        self.is_pulse = True
        self.Refresh()

    def on_paint(self, event):
        w, h = self.GetSize()
        dc = wx.PaintDC(self)
        if self.is_pulse:
            set_pen(
                dc,
                self.default_color,
                width=h,
                style=wx.PENSTYLE_SHORT_DASH
            )
            dc.DrawLine(0, 0, w, 0)
        else:
            w_fg = round(w * self.fraction)
            set_pen(dc, self.color, width=h)
            dc.DrawLine(0, 0, w_fg, 0)
            set_pen(dc, self.default_color, width=h)
            dc.DrawLine(w_fg, 0, w, 0)


class Menu(wx.PopupTransientWindow):
    store: Store
    panel: wx.Panel
    border_sizer: wx.BoxSizer
    sizer: wx.BoxSizer
    radio_buttons: List[wx.RadioButton]
    progress_bars: Dict[Path, wx.Gauge]
    spinner: wx.StaticText
    mouse_x: int = 0
    mouse_y: int = 0
    last_fractions: Optional[TFractions] = None

    def __init__(self, store: Store, parent: wx.Window, *args, **kwargs):
        super().__init__(*args, parent=parent, **kwargs)
        self.store = store
        self._init()

    def _init(self):
        self._init_window()
        if self.store.directories:
            self._init_radio_buttons()
            self._init_progress_bars()
            self._init_spinner()
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

    def _init_radio_buttons(self):
        self.radio_buttons = []
        grid = wx.GridSizer(cols=2, vgap=0, hgap=10)
        for name, label, tooltip in [
            (
                SIZE_MODE_SIZE,
                'by size',
                (
                    'Each bar shows the fraction of the total root directory '
                    'size that the given directory occupies.'
                )
            ),
            (
                SIZE_MODE_SIZE_NEW,
                'by activity',
                (
                    'Each bar shows the fraction of the size of the given '
                    'directory that was modified in the last 30 days.'
                )
            ),
        ]:
            button = wx.ToggleButton(parent=self, label=label)
            button.SetValue(name == self.store.active_mode)
            button.Bind(
                wx.EVT_TOGGLEBUTTON,
                partial(self._on_radio_toggled, button=button, mode=name)
            )
            grid.Add(button)
            self.radio_buttons.append(button)
        self.sizer.Add(grid)

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
        self.sizer.AddSpacer(10)
        for i, path in enumerate(self.store.directories.keys()):
            label = create_label(self, self.store.get_text(path))
            progress_bar = Gauge(parent=self, color=color_from_index(i))
            fraction = self.store.fractions[path]
            if fraction is not None:
                progress_bar.set_fraction(fraction)
            self.sizer.Add(label, flag=wx.EXPAND | wx.BOTTOM, border=3)
            self.sizer.Add(progress_bar, flag=wx.EXPAND | wx.BOTTOM, border=5)
            self.progress_bars[path] = progress_bar

    def _init_spinner(self):
        self.spinner = create_label(self, 'calculating...')
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
        self.DestroyChildren()

    def refresh(self):
        self._empty()
        self._init()
        self._position()

    def update(self, pulse: bool = False):
        if (self.store.directories
                and self.store.fractions != self.last_fractions):
            self.last_fractions = self.store.fractions
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
        if self.store.active_mode == mode:
            button.SetValue(True)
            return
        self.store.set_active_mode(mode)
        for other_button in self.radio_buttons:
            if other_button != button:
                other_button.SetValue(False)
        self.update(pulse=False)

    def _on_setup_button(self, event):
        self.Dismiss()
        setup = Setup(self, self.store.config)
        if setup.run():
            self.store.config = setup.config
            self.refresh()
            save_config(self.store.config)

    def ProcessLeftDown(self, event):
        logger.info('ProcessLeftDown: %s' % event.GetPosition())
        return wx.PopupTransientWindow.ProcessLeftDown(self, event)
