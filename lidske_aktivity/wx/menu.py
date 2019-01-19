import logging
import time
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

import wx

from lidske_aktivity.icon import color_from_index
from lidske_aktivity.model import SIZE_MODES, DirectoryView
from lidske_aktivity.wx.lib import create_button, create_label, create_sizer

if TYPE_CHECKING:
    from lidske_aktivity.app import Application

logger = logging.getLogger(__name__)


def set_pen(dc: wx.PaintDC, color_index: int, *args, **kwargs):
    color = color_from_index(color_index)
    pen = wx.Pen(*args, color, **kwargs)
    pen.SetJoin(wx.JOIN_MITER)
    pen.SetCap(wx.CAP_BUTT)
    dc.SetPen(pen)


class ProgressBar(wx.BoxSizer):
    i: int
    label: wx.StaticText
    bar: wx.Window
    fraction: float = 0
    is_pulse: bool = True

    def __init__(self, parent: wx.Window, text: str, i: int):
        super().__init__(wx.VERTICAL)
        self.i = i
        self.label = create_label(parent, text)
        self.bar = wx.Window(parent, size=(-1, 6))
        self.bar.Bind(wx.EVT_PAINT, self.on_paint)
        self.Add(self.label, flag=wx.EXPAND | wx.BOTTOM, border=3)
        self.Add(self.bar, flag=wx.EXPAND | wx.BOTTOM, border=5)

    def set_fraction(self, fraction: float, tooltip: str):
        self.is_pulse = False
        self.fraction = fraction
        self.label.SetToolTip(tooltip)
        self.bar.SetToolTip(tooltip)
        self.bar.Refresh()

    def pulse(self):
        self.is_pulse = True
        self.label.SetToolTip('calculating...')
        self.bar.SetToolTip('calculating...')
        self.bar.Refresh()

    def on_paint(self, event):
        w, h = self.bar.GetSize()
        dc = wx.PaintDC(self.bar)
        if self.is_pulse:
            set_pen(
                dc,
                color_index=-1,
                width=h,
                style=wx.PENSTYLE_SHORT_DASH
            )
            dc.DrawLine(0, 0, w, 0)
        else:
            w_fg = round(w * self.fraction)
            set_pen(dc, color_index=self.i, width=h)
            dc.DrawLine(0, 0, w_fg, 0)
            set_pen(dc, color_index=-1, width=h)
            dc.DrawLine(w_fg, 0, w, 0)


class Menu(wx.PopupTransientWindow):
    app: 'Application'
    active_mode: str
    panel: wx.Panel
    border_sizer: wx.BoxSizer
    sizer: wx.BoxSizer
    radio_buttons: Dict[str, wx.RadioButton]
    progress_bars: Dict[Path, ProgressBar]
    spinner: wx.StaticText
    mouse_x: int = 0
    mouse_y: int = 0
    last_closed: float = 0

    def __init__(self, app: 'Application', parent: wx.Frame):
        super().__init__(parent)
        self.app = app

    def init(self, active_mode: str, directory_views: List[DirectoryView]):
        self._init_window()
        if directory_views:
            self._init_radio_buttons()
            self.update_radio_buttons(active_mode)
            self._init_progress_bars(directory_views)
        else:
            self._init_empty()
        self._init_spinner()
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
        self.radio_buttons = {}
        grid = wx.GridSizer(cols=2, vgap=0, hgap=10)
        for mode in SIZE_MODES:
            button = wx.ToggleButton(parent=self.panel, label=mode.label)
            button.SetToolTip(mode.tooltip)
            button.Bind(
                wx.EVT_TOGGLEBUTTON,
                partial(self._on_radio_toggled, button=button, mode=mode.name)
            )
            grid.Add(button)
            self.radio_buttons[mode.name] = button
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

    def _init_progress_bars(self, directory_views: List[DirectoryView]):
        self.progress_bars = {}
        self.sizer.AddSpacer(10)
        for i, directory_view in enumerate(directory_views):
            progress_bar = ProgressBar(
                parent=self.panel,
                text=directory_view.directory.label,
                i=i
            )
            self.sizer.Add(progress_bar, flag=wx.EXPAND)
            self.progress_bars[directory_view.directory.path] = progress_bar

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

    def pulse_progress_bar(self, path: Path):
        self.progress_bars[path].pulse()

    def update_progress_bar(self, path: Path, fraction: float, tooltip: str):
        self.progress_bars[path].set_fraction(fraction, tooltip)

    def hide_spinner(self):
        self.spinner.Hide()
        self._fit()

    def reset(self, active_mode: str, directory_views: List[DirectoryView]):
        self._empty()
        self.init(active_mode, directory_views)
        self._position()

    def popup_at(self, mouse_x: int, mouse_y: int):
        if self.IsShown():
            logger.info('Popup menu: doing nothing, menu is already open')
            return
        if self._was_just_closed():
            logger.info('Popup menu: doing nothing, menu was just closed')
            return
        logger.info('Popup menu at %s x %s', mouse_x, mouse_y)
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
        logger.info('Radio toggled: new mode = "%s"', mode)
        self.app.set_active_mode(mode)

    def update_radio_buttons(self, active_mode: str):
        for mode, radio_button in self.radio_buttons.items():
            radio_button.SetValue(mode == active_mode)

    def _on_setup_button(self):
        self.Dismiss()
        self.app.show_setup()

    def _was_just_closed(self, threshold_seconds: float = 1) -> bool:
        """Was the menu closed less than threshold_seconds ago?

        Used to fix the case on Windows, where ProcessLeftDown() is triggered
        before popup_at(), which causes the menu to close and immediatelly
        open again when the user clicks on the tray icon.
        """
        diff = time.time() - self.last_closed

        # Don't leave the menu forever closed when the system time changed.
        self.last_closed = 0

        return diff < threshold_seconds

    def ProcessLeftDown(self, event: wx.MouseEvent):
        logger.info('Click outside menu')
        self.last_closed = time.time()
        return super().ProcessLeftDown(event)

    def destroy(self):
        self.Destroy()
