import io
import logging
from typing import Callable

import wx
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


def create_icon_from_image(image: Image) -> wx.Icon:
    with io.BytesIO() as f:
        image.save(f, format='PNG')
        f.seek(0)
        wx_image = wx.Image(f)
        icon = wx.Icon(wx_image.ConvertToBitmap())
    return icon


def call_tick(func: Callable):
    wx.CallAfter(func)
