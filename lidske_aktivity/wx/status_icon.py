from typing import TYPE_CHECKING, List

import wx
import wx.adv

from lidske_aktivity.icon import draw_pie_chart
from lidske_aktivity.model import DirectoryView
from lidske_aktivity.wx.lib import create_icon_from_image, new_id_ref_compat

if TYPE_CHECKING:
    from lidske_aktivity.app import Application


def add_menu_item(menu: wx.Menu, text: str, tooltip: str = ''):
    menu_item = wx.MenuItem(menu, wx.ID_ANY, text, helpString=tooltip)
    menu.Append(menu_item)
    menu_item.Enable(False)
    return menu_item


class StatusIcon(wx.adv.TaskBarIcon):
    app: 'Application'
    id_setup = new_id_ref_compat()
    _menu: wx.Menu

    def __init__(self, app: 'Application'):
        super().__init__(wx.adv.TBI_DOCK)
        self.app = app
        self.Bind(
            wx.adv.EVT_TASKBAR_LEFT_DOWN,
            lambda event: self._show_menu()
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
        self._init_menu([])

    def _init_menu(self, directory_views: List[DirectoryView]):
        # TODO: Limit the maximum number of items shown.
        menu = wx.Menu()
        if directory_views:
            for directory_view in directory_views:
                add_menu_item(
                    menu,
                    directory_view.text,
                    directory_view.tooltip
                )
        else:
            add_menu_item(menu, 'No directories configured')
            menu.AppendSeparator()
            menu.Append(self.id_setup, '&Setup')
        self._menu = menu

    def _show_menu(self):
        self.PopupMenu(self._menu)

    def CreatePopupMenu(self) -> wx.Menu:
        context_menu = wx.Menu()
        context_menu.Append(self.id_setup, '&Setup')
        context_menu.Append(wx.ID_SETUP, 'Advanced &configuration')
        context_menu.Append(wx.ID_ABOUT, '&About')
        context_menu.Append(wx.ID_EXIT, '&Quit')
        return context_menu

    def update(self, directory_views: List[DirectoryView]):
        percents = (dv.fraction for dv in directory_views)
        texts = (dv.text for dv in directory_views)
        image = draw_pie_chart(self.icon_size, percents)
        icon = create_icon_from_image(image)
        tooltip = '\n'.join(texts)
        self.SetIcon(icon, tooltip)
        self._init_menu(directory_views)

    @property
    def icon_size(self) -> int:
        if 'wxMSW' in wx.PlatformInfo:
            return 16
        if 'wxGTK' in wx.PlatformInfo:
            return 22
        return 128

    def destroy(self):
        self.Destroy()
