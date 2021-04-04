from functools import partial
from typing import TYPE_CHECKING, Callable, Optional, Tuple

import wx
import wx.adv
from PIL import Image

from human_activities import __title__, texts
from human_activities.icon import DEFAULT_FRACTIONS, draw_pie_chart_png
from human_activities.l10n import _
from human_activities.model import DirectoryViews
from human_activities.wx.lib import (
    image_to_bitmap,
    image_to_icon,
    new_id_ref_compat,
)

if TYPE_CHECKING:
    from human_activities.app import Application


def create_menu_item(
    parent: wx.Window,
    menu: wx.Menu,
    text: str,
    tooltip: str = '',
    icon_image: Optional[Image.Image] = None,
    id: int = wx.ID_ANY,
    callback: Optional[Callable] = None,
):
    """Create menu item

    The tooltip is actually not visible, menu items with tooltips are not
    supported by WxWidgets.
    """
    menu_item = wx.MenuItem(menu, id, text, helpString=tooltip)
    if icon_image:
        bitmap = image_to_bitmap(icon_image)
        menu_item.SetBitmap(bitmap)
    menu.Append(menu_item)
    if callback:
        parent.Bind(
            wx.EVT_MENU, partial(on_menu_item, callback=callback), id=id
        )
    else:
        menu_item.Enable(False)
    return menu_item


def on_menu_item(event: wx.MouseEvent, callback: Callable):
    callback()


class StatusIcon(wx.adv.TaskBarIcon):
    app: 'Application'
    id_setup = new_id_ref_compat()
    _menu: wx.Menu
    _last_fractions: Optional[Tuple[float, ...]] = None
    _last_icon: Optional[wx.Icon] = None

    def __init__(self, app: 'Application'):
        super().__init__(wx.adv.TBI_DOCK)
        self.app = app
        self.Bind(
            wx.adv.EVT_TASKBAR_LEFT_DOWN, lambda event: self._show_menu()
        )
        self._init_menu()
        self._set_icon(DEFAULT_FRACTIONS, __title__)

    def _init_menu(self, directory_views: Optional[DirectoryViews] = None):
        menu = wx.Menu()
        if directory_views:
            for i, directory_view in enumerate(directory_views.values()):
                icon_image = draw_pie_chart_png(
                    16, directory_views.fractions, highlighted=i
                )
                create_menu_item(
                    self, menu, directory_view.text, icon_image=icon_image
                )
            if directory_views.configured_dirs.truncated:
                create_menu_item(
                    self,
                    menu,
                    texts.MENU_DIRS_TRUNCATED.format(
                        max_len=directory_views.configured_dirs.max_len
                    ),
                )
            if directory_views.threshold_days_ago:
                menu.AppendSeparator()
                create_menu_item(
                    self,
                    menu,
                    texts.MENU_THRESHOLD_DAYS_AGO.format(
                        days=directory_views.threshold_days_ago
                    ),
                )
        else:
            create_menu_item(self, menu, texts.MENU_EMPTY)
            menu.AppendSeparator()
            create_menu_item(
                self,
                menu,
                _('&Setup'),
                id=self.id_setup,
                callback=self.app.show_setup,
            )
        self._menu = menu

    def _show_menu(self):
        self.PopupMenu(self._menu)

    def CreatePopupMenu(self) -> wx.Menu:
        context_menu = wx.Menu()
        create_menu_item(
            self,
            context_menu,
            _('&Setup'),
            id=self.id_setup,
            callback=self.app.show_setup,
        )
        create_menu_item(
            self,
            context_menu,
            _('Advanced &configuration'),
            id=wx.ID_SETUP,
            callback=self.app.show_settings,
        )
        create_menu_item(
            self,
            context_menu,
            _('&About'),
            id=wx.ID_ABOUT,
            callback=self.app.show_about,
        )
        create_menu_item(
            self,
            context_menu,
            _('&Quit'),
            id=wx.ID_EXIT,
            callback=self.app.quit,
        )
        return context_menu

    def update(self, directory_views: DirectoryViews):
        wx.CallAfter(partial(self._on_update, directory_views))

    def _on_update(self, directory_views: DirectoryViews):
        self._init_menu(directory_views)
        self._set_icon(directory_views.fractions, directory_views.tooltip)

    def _set_icon(self, fractions: Tuple[float, ...], tooltip: str):
        if self._last_fractions == fractions and self._last_icon:
            icon = self._last_icon
        else:
            image = draw_pie_chart_png(self.icon_size, fractions)
            icon = image_to_icon(image)
            self._last_fractions = fractions
            self._last_icon = icon
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
