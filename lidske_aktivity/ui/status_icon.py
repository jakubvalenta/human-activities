from typing import TYPE_CHECKING

import wx
import wx.adv
from PIL import Image

from lidske_aktivity.ui.lib import create_icon_from_image, new_id_ref_compat

if TYPE_CHECKING:
    from lidske_aktivity.app import Application


class StatusIcon(wx.adv.TaskBarIcon):
    app: 'Application'
    id_setup = new_id_ref_compat()

    def __init__(self, app: 'Application'):
        # TODO: Check TaskBarIcon.isAvailable()
        super().__init__(wx.adv.TBI_DOCK)
        self.app = app
        self.Bind(
            wx.adv.EVT_TASKBAR_LEFT_DOWN,
            lambda event: self.app.show_menu(*wx.GetMousePosition())
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
