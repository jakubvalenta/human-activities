from typing import Callable

import wx
import wx.adv
from PIL import Image

from lidske_aktivity.ui.lib import create_icon_from_image, new_id_ref_compat


class App(wx.App):
    pass


class StatusIcon(wx.adv.TaskBarIcon):
    id_setup = new_id_ref_compat()

    def __init__(self,
                 on_menu: Callable,
                 on_setup: Callable,
                 on_settings: Callable,
                 on_about: Callable,
                 on_quit: Callable):
        # TODO: Check TaskBarIcon.isAvailable()
        super().__init__(wx.adv.TBI_DOCK)
        self.update()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, on_menu)
        self.Bind(wx.EVT_MENU, on_setup, id=self.id_setup)
        self.Bind(wx.EVT_MENU, on_settings, id=wx.ID_SETUP)
        self.Bind(wx.EVT_MENU, on_about, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, on_quit, id=wx.ID_EXIT)

    def CreatePopupMenu(self) -> wx.Menu:
        menu = wx.Menu()
        menu.Append(self.id_setup, '&Setup')
        menu.Append(wx.ID_SETUP, 'Advanced &configuration')
        menu.Append(wx.ID_ABOUT, '&About')
        menu.Append(wx.ID_EXIT, 'E&xit')
        return menu

    def update_icon(self, image: Image, tooltip: str):
        icon = create_icon_from_image(image)
        self.SetIcon(icon, tooltip)

    @staticmethod
    def calc_icon_size() -> int:
        if 'wxMSW' in wx.PlatformInfo:
            return 16
        if 'wxGTK' in wx.PlatformInfo:
            return 22
        return 128
