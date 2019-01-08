import io
import logging
import time
from functools import partial
from pathlib import Path
from threading import Event, Thread
from typing import Callable, Dict, List, Optional

import wx
import wx.adv
from PIL import Image

from lidske_aktivity.bitmap import TColor, color_from_index

logger = logging.getLogger(__name__)


def new_id_ref_compat():
    """A wrapper around wx.NewIdRef() compatible with wxPython < 4.0.3"""
    try:
        return wx.NewIdRef()
    except AttributeError:
        return wx.NewId()


def create_sizer(parent: wx.Window,
                 orientation: int = wx.VERTICAL,
                 *args,
                 **kwargs) -> wx.BoxSizer:
    sizer = wx.BoxSizer(orientation)
    if isinstance(parent, wx.Sizer):
        parent.Add(sizer, *args, **kwargs)
    else:
        parent.SetSizer(sizer)
    return sizer


def create_label(parent: wx.Window, text: str) -> wx.StaticText:
    return wx.StaticText(parent, label=text)


def create_button(parent: wx.Window,
                  panel: wx.Panel,
                  label: str,
                  callback: Callable) -> wx.Button:
    button = wx.Button(panel, wx.ID_ANY, label)
    parent.Bind(wx.EVT_BUTTON, callback, id=button.GetId())
    return button


def create_text_control(parent: wx.Window,
                        value: str,
                        callback: Callable) -> wx.TextCtrl:
    text_control = wx.TextCtrl(parent, value=value)
    parent.Bind(wx.EVT_TEXT, callback, text_control)
    return text_control


def choose_dir(parent: wx.Window, callback: Callable[[str], None]):
    dialog = wx.DirDialog(
        parent,
        'Choose a directory:',
        style=wx.DD_DIR_MUST_EXIST
        # TODO: Fill in current dir
    )
    if dialog.ShowModal() == wx.ID_OK:
        path = dialog.GetPath()
        callback(path)


def add_text_heading(parent: wx.Window, sizer: wx.Sizer, text: str):
    label = create_label(parent, text)
    sizer.Add(label, flag=wx.BOTTOM, border=10)


def add_text_paragraph(parent: wx.Window, sizer: wx.Sizer, text: str):
    label = create_label(parent, text)
    sizer.Add(label, flag=wx.BOTTOM, border=5)


def add_text_list(parent: wx.Window, sizer: wx.Sizer, items: List[str]):
    for item in items:
        label = create_label(parent, f'\N{BULLET} {item}')
        sizer.Add(label)
    sizer.AddSpacer(5)


def set_pen(dc: wx.PaintDC, *args, **kwargs):
    pen = wx.Pen(*args, **kwargs)
    pen.SetJoin(wx.JOIN_MITER)
    pen.SetCap(wx.CAP_BUTT)
    dc.SetPen(pen)


def create_icon_from_image(image: Image) -> wx.Icon:
    with io.BytesIO() as f:
        image.save(f, format='PNG')
        f.seek(0)
        image = wx.Image(f)
        icon = wx.Icon(image.ConvertToBitmap())
    return icon


def show_about(image: Image,
               title: str,
               version: str,
               copyright: str,
               uri: str,
               authors: List[str]):
    info = wx.adv.AboutDialogInfo()
    info.Icon = create_icon_from_image(image)
    info.Name = title
    info.Version = version
    info.Copyright = copyright
    info.WebSite = uri
    info.Developers = authors
    wx.adv.AboutBox(info)


class ProgressBar(wx.BoxSizer):
    label: wx.StaticText
    bar: wx.Window
    color: TColor
    fraction: float = 0
    is_pulse: bool = True
    default_color: TColor = (147, 161, 161, 255)

    def __init__(self, parent: wx.Window, text: str, color: TColor):
        super().__init__(wx.VERTICAL)
        self.color = color
        self.label = create_label(parent, text)
        self.bar = wx.Window(parent, size=(-1, 5))
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
        self.label.SetToolTip('Calculating...')
        self.bar.SetToolTip('Calculating...')
        self.bar.Refresh()

    def on_paint(self, event):
        w, h = self.bar.GetSize()
        dc = wx.PaintDC(self.bar)
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
    app: 'Application'
    panel: wx.Panel
    border_sizer: wx.BoxSizer
    sizer: wx.BoxSizer
    radio_buttons: List[wx.RadioButton]
    progress_bars: Dict[Path, ProgressBar]
    spinner: wx.StaticText
    mouse_x: int = 0
    mouse_y: int = 0
    last_closed: float = 0

    def __init__(self, app: 'Application', *args, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)

    def init(self, app: 'Application'):
        self._init_window()
        if self.app.directories:
            self._init_radio_buttons()
            self._init_progress_bars()
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
        self.radio_buttons = []
        grid = wx.GridSizer(cols=2, vgap=0, hgap=10)
        for mode in self.app.modes:
            button = wx.ToggleButton(parent=self.panel, label=mode.label)
            button.SetValue(mode.name == self.app.active_mode)
            button.SetToolTip(mode.tooltip)
            button.Bind(
                wx.EVT_TOGGLEBUTTON,
                partial(self._on_radio_toggled, button=button, mode=mode.name)
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
        for i, path in enumerate(self.app.directories.keys()):
            progress_bar = ProgressBar(
                parent=self.panel,
                text=self.app.get_text(path),
                color=color_from_index(i)
            )
            self.sizer.Add(progress_bar, flag=wx.EXPAND)
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

    def pulse_progress_bar(self, path: Path):
        self.progress_bars[path].pulse()

    def update_progress_bar(self, path: Path, fraction: float, tooltip: str):
        self.progress_bars[path].set_fraction(fraction, tooltip)

    def hide_spinner(self):
        self.spinner.Hide()
        self._fit()

    def reset(self):
        self._empty()
        self._init()
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
        logger.info('Radio toggled: "%s" > "%s"', self.app.active_mode, mode)
        if self.app.active_mode == mode:
            button.SetValue(True)
            return
        for other_button in self.radio_buttons:
            if other_button != button:
                other_button.SetValue(False)
        self.app.active_mode = mode

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
        return super().ProcessLeftDown(self, event)

    def destroy(self):
        self.Destroy()


class StatusIcon(wx.adv.TaskBarIcon):
    app: 'Application'
    id_setup = new_id_ref_compat()

    def __init__(self, app: 'Application'):
        # TODO: Check TaskBarIcon.isAvailable()
        super().__init__(wx.adv.TBI_DOCK)
        self.app = app
        self.Bind(
            wx.adv.EVT_TASKBAR_LEFT_DOWN,
            lambda: self.app.show_menu(*wx.GetMousePosition())
        )
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.app.show_setup(),
            id=self.id_setup
        )
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.app.show_settings(),
            id=wx.ID_SETUP
        )
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.app.show_about(),
            id=wx.ID_ABOUT
        )
        self.Bind(
            wx.EVT_MENU,
            lambda event: self.app.quit(),
            id=wx.ID_EXIT
        )

    def CreatePopupMenu(self) -> wx.Menu:
        context_menu = wx.Menu()
        context_menu.Append(self.id_setup, '&Setup')
        context_menu.Append(wx.ID_SETUP, 'Advanced &configuration')
        context_menu.Append(wx.ID_ABOUT, '&About')
        context_menu.Append(wx.ID_EXIT, 'E&xit')
        return context_menu

    def update(self, image: Image, tooltip: str):
        icon = create_icon_from_image(image)
        self.SetIcon(icon, tooltip)

    @property
    def icon_size(self) -> int:
        if 'wxMSW' in wx.PlatformInfo:
            return 16
        if 'wxGTK' in wx.PlatformInfo:
            return 22
        return 128

    def destroy(self):
        self.Destroy()


class Application(wx.App):
    title: str
    frame: wx.Frame

    tick_event_stop: Optional[Event] = None
    tick_thread: Optional[Thread] = None

    def __init__(self, *args, **kwargs):
        super().__init__(False, *args, **kwargs)

    def OnInit(self) -> bool:
        self.frame = wx.Frame(parent=None, title=self.title)
        self.on_init()
        self._tick_start()
        return True

    def on_init(self):
        raise NotImplementedError

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
            logger.info('Updating UI')
            wx.CallAfter(self.on_tick)
            time.sleep(1)

    def on_tick(self):
        raise NotImplementedError

    def quit(self):
        logger.info('Menu quit')
        self._tick_stop()
        self.frame.Destroy()

    def OnExit(self):
        logger.info('App OnExit')
        self._tick_stop()
        self.on_exit()
        super().OnExit()
        return True

    def on_exit(self):
        raise NotImplementedError

    def run(self):
        self.MainLoop()
