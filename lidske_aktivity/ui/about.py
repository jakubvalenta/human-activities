from typing import List

import wx.adv
from PIL import Image

from lidske_aktivity.ui.lib import create_icon_from_image


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
