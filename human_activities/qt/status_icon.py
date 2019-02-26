import logging
from typing import TYPE_CHECKING, Callable, Optional, Tuple

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMenu, QStyle, QSystemTrayIcon

from human_activities import __title__, is_mac, is_win, texts
from human_activities.icon import DEFAULT_FRACTIONS, draw_pie_chart_png
from human_activities.locale import _
from human_activities.model import DirectoryViews
from human_activities.qt.lib import create_icon, get_icon_size, image_to_pixmap

if TYPE_CHECKING:
    from human_activities.app import Application

logger = logging.getLogger(__name__)


def create_menu_item(
    menu: QMenu,
    label: str,
    callback: Optional[Callable] = None,
    tooltip: Optional[str] = None,
    icon_pixmap: Optional[QPixmap] = None,
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


class StatusIcon(QSystemTrayIcon):
    app: 'Application'
    _last_fractions: Optional[Tuple[float, ...]] = None
    _update_signal = pyqtSignal(DirectoryViews)

    def __init__(self, app: 'Application'):
        self.app = app
        super().__init__(parent=self.app._ui_app)
        self._update_signal.connect(self._on_update)
        self._init_menu()
        self._set_icon(DEFAULT_FRACTIONS, __title__)
        self.show()

    def _init_menu(self, directory_views: Optional[DirectoryViews] = None):
        menu = QMenu(parent=None)
        if directory_views:
            for i, directory_view in enumerate(directory_views.values()):
                icon_size = get_icon_size(
                    self.app._ui_app, QStyle.PM_SmallIconSize
                )
                icon_image = draw_pie_chart_png(
                    icon_size, directory_views.fractions, highlighted=i
                )
                icon_pixmap = image_to_pixmap(icon_image)
                create_menu_item(
                    menu, directory_view.text, icon_pixmap=icon_pixmap
                )
            if directory_views.configured_dirs.truncated:
                create_menu_item(
                    menu,
                    texts.MENU_DIRS_TRUNCATED.format(
                        max_len=directory_views.configured_dirs.max_len
                    ),
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
        create_menu_item(menu, _('&About'), callback=self.app.show_about)
        create_menu_item(menu, _('&Quit'), callback=self.app.quit)
        self.setContextMenu(menu)

    def update(self, directory_views: DirectoryViews):
        self._update_signal.emit(directory_views)

    def _on_update(self, directory_views: DirectoryViews):
        logger.info('Qt StatusIcon on_update')
        self._init_menu(directory_views)
        self._set_icon(directory_views.fractions, directory_views.tooltip)

    def _set_icon(self, fractions: Tuple[float, ...], tooltip: str):
        if self._last_fractions != fractions:
            image = draw_pie_chart_png(self.icon_size, fractions)
            pixmap = image_to_pixmap(image)
            icon = create_icon(pixmap)
            self.setIcon(icon)
            self._last_fractions = fractions
        self.setToolTip(tooltip)

    @property
    def icon_size(self) -> int:
        if is_win():
            return 16
        elif is_mac():
            return 22
        return 128

    def destroy(self):
        pass
