from typing import TYPE_CHECKING, Callable

import gi
from PIL import Image

from lidske_aktivity.gtk.lib import create_menu_item

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import AppIndicator3, Gtk  # noqa:E402  # isort:skip


if TYPE_CHECKING:
    from lidske_aktivity.app import Application


def create_context_menu(on_about: Callable, on_quit: Callable) -> Gtk.Menu:
    context_menu = Gtk.Menu()
    context_menu.show_all()
    return context_menu


class StatusIcon():
    app: 'Application'
    _indicator: AppIndicator3.Indicator
    icon_size = 22

    def __init__(self, app: 'Application'):
        self.app = app
        create_menu_item(
            self.app.menu,
            'Setup',
            lambda event: self.app.show_setup()
        )
        create_menu_item(
            self.app.menu,
            'Advanced configuration',
            lambda event: self.app.show_settings()
        )
        create_menu_item(
            self.app.menu,
            'Quit',
            lambda event: self.app.quit
        )
        self._indicator = AppIndicator3.Indicator.new(
            'lidske-aktivity',
            '',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_menu(self.app.menu)

    def update(self, image: Image, tooltip: str):
        # TODO: icon = create_icon_from_image(image)
        self._indicator.set_icon('application-exit')
        self._indicator.set_label(tooltip, tooltip)

    def destroy(self):
        self._indicator.show(False)
