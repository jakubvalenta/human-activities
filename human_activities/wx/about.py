from typing import List

import wx.adv
from PIL import Image

from human_activities.wx.lib import image_to_icon


def show_about(
    image: Image.Image,
    title: str,
    version: str,
    copyright: str,
    uri: str,
    authors: List[str],
):
    info = wx.adv.AboutDialogInfo()
    info.Icon = image_to_icon(image)
    info.Name = title
    info.Version = version
    info.Copyright = copyright
    info.WebSite = uri
    info.Developers = authors
    wx.adv.AboutBox(info)
