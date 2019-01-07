import io
import logging
from threading import Event, Thread
from time import sleep
from typing import Callable, List, Optional

import wx
import wx.adv
from PIL import Image

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
            sleep(1)

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


class StatusIcon(wx.adv.TaskBarIcon):
    menu: Menu
    id_setup = new_id_ref_compat()

    def __init__(self,
                 on_setup: Callable,
                 on_settings: Callable,
                 on_about: Callable,
                 on_quit: Callable):
        # TODO: Check TaskBarIcon.isAvailable()
        super().__init__(wx.adv.TBI_DOCK)
        self.update()
        self.menu = Menu(store=self.store, parent=self.frame)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self._show_menu)
        self.Bind(wx.EVT_MENU, lambda event: on_setup(), id=self.id_setup)
        self.Bind(wx.EVT_MENU, lambda event: on_settings(), id=wx.ID_SETUP)
        self.Bind(wx.EVT_MENU, lambda event: on_about(), id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, lambda event: on_quit(), id=wx.ID_EXIT)

    def CreatePopupMenu(self) -> wx.Menu:
        menu = wx.Menu()
        menu.Append(self.id_setup, '&Setup')
        menu.Append(wx.ID_SETUP, 'Advanced &configuration')
        menu.Append(wx.ID_ABOUT, '&About')
        menu.Append(wx.ID_EXIT, 'E&xit')
        return menu

    def _show_menu(self):
        self.menu.popup_at(*wx.GetMousePosition())

    def update_icon(self, image: Image, tooltip: str):
        icon = create_icon_from_image(image)
        self.SetIcon(icon, tooltip)

    def update_menu(self):
        self.menu.update()

    def refresh_menu(self):
        self.menu.refresh()

    @staticmethod
    def calc_icon_size() -> int:
        if 'wxMSW' in wx.PlatformInfo:
            return 16
        if 'wxGTK' in wx.PlatformInfo:
            return 22
        return 128

    def destroy(self):
        self.Destroy()
        self.menu.Destroy()
