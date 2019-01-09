from typing import List

import wx.adv

from lidske_aktivity.bitmap import draw_pie_chart, gen_random_slices
from lidske_aktivity.wx.lib import create_icon_from_image


def show_about(title: str,
               version: str,
               copyright: str,
               uri: str,
               authors: List[str]):
    info = wx.adv.AboutDialogInfo()
    image = draw_pie_chart(148, list(gen_random_slices()))
    info.Icon = create_icon_from_image(image)
    info.Name = title
    info.Version = version
    info.Copyright = copyright
    info.WebSite = uri
    info.Developers = authors
    wx.adv.AboutBox(info)
