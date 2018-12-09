import io
from typing import Callable, List

import wx
from PIL import Image


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
