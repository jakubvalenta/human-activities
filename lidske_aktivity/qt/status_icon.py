import logging
from typing import TYPE_CHECKING, Callable, Optional, Tuple

from PyQt5 import QtWidgets, QtGui

from lidske_aktivity import texts, is_win, is_mac
from lidske_aktivity.icon import draw_pie_chart_png
from lidske_aktivity.locale import _
from lidske_aktivity.model import DirectoryViews
from lidske_aktivity.qt.lib import (
    get_icon_size,
    create_icon_pixmap,
    image_to_pixmap,
    create_icon,
)

if TYPE_CHECKING:
    from lidske_aktivity.app import Application

logger = logging.getLogger(__name__)


def create_menu_item(
    menu: QtWidgets.QMenu,
    label: str,
    callback: Optional[Callable] = None,
    tooltip: Optional[str] = None,
    icon_pixmap: Optional[QtGui.QPixmap] = None,
):
    action = menu.addAction(label)
    if icon_pixmap:
        icon = create_icon(icon_pixmap)
        action.setIcon(icon)
    if tooltip:
        action.setToolTip(tooltip)
    if callback:
        action.triggered.connect(callback)
    else:
        action.setEnabled(False)


class StatusIcon(QtWidgets.QSystemTrayIcon):
    app: 'Application'
    _last_fractions: Optional[Tuple[float, ...]] = None

    def __init__(self, app: 'Application'):
        self.app = app
        super().__init__(parent=None)
        self._init_menu()

    def _init_menu(self, directory_views: Optional[DirectoryViews] = None):
        menu = QtWidgets.QMenu(parent=None)
        # TODO: Limit the maximum number of items shown.
        if directory_views:
            for i, directory_view in enumerate(directory_views.values()):
                icon_size = get_icon_size(
                    self.app._ui_app, QtWidgets.QStyle.PM_SmallIconSize
                )
                icon_image = draw_pie_chart_png(
                    icon_size,
                    directory_views.fractions,
                    directory_views.get_colors_with_one_highlighted(i),
                )
                icon_pixmap = image_to_pixmap(icon_image)
                create_menu_item(
                    menu, directory_view.text, icon_pixmap=icon_pixmap
                )
            if directory_views.threshold_days_ago:
                menu.addSeparator()
                create_menu_item(
                    menu,
                    texts.MENU_THRESHOLD_DAYS_AGO.format(
                        days=directory_views.threshold_days_ago
                    ),
                )
        else:
            create_menu_item(menu, texts.MENU_EMPTY)
        menu.addSeparator()
        create_menu_item(menu, _('&Setup'), callback=self.app.show_setup)
        create_menu_item(
            menu, _('Advanced &configuration'), callback=self.app.show_settings
        )
        create_menu_item(
            menu,
            _('&About'),
            callback=self.app.show_about,
            icon_pixmap=create_icon_pixmap(
                self.app._ui_app, QtWidgets.QStyle.SP_DialogHelpButton
            ),
        )
        create_menu_item(
            menu,
            _('&Quit'),
            callback=self.app.quit,
            icon_pixmap=create_icon_pixmap(
                self.app._ui_app, QtWidgets.QStyle.SP_DialogCloseButton
            ),
        )
        self.setContextMenu(menu)

    def update(self, directory_views: DirectoryViews):
        self._init_menu(directory_views)
        if self._last_fractions == directory_views.fractions:
            return
        self._last_fractions = directory_views.fractions
        image = draw_pie_chart_png(self.icon_size, directory_views.fractions)
        pixmap = image_to_pixmap(image)
        icon = create_icon(pixmap)
        self.setIcon(icon)
        self.setToolTip(directory_views.tooltip)
        self.show()

    @property
    def icon_size(self) -> int:
        if is_win():
            return 16
        elif is_mac():
            return 22
        return 128

    def destroy(self):
        pass
