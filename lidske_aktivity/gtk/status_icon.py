import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, List

import gi

from lidske_aktivity import __application_id__, __application_name__
from lidske_aktivity.bitmap import draw_pie_chart_svg
from lidske_aktivity.gtk.lib import create_menu_item

logger = logging.getLogger(__name__)


gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import AppIndicator3, Gtk  # noqa:E402  # isort:skip

if TYPE_CHECKING:
    from lidske_aktivity.app import Application


def create_context_menu(on_about: Callable, on_quit: Callable) -> Gtk.Menu:
    context_menu = Gtk.Menu()
    context_menu.show_all()
    return context_menu


def write_temp_file(lines: Iterable[str],
                    filename: str,
                    **kwargs) -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory(**kwargs)
    with (Path(temp_dir.name) / filename).open('w') as f:
        f.writelines(lines)
    return temp_dir


class StatusIcon():
    app: 'Application'
    _indicator: AppIndicator3.Indicator
    icon_temp_dir: tempfile.TemporaryDirectory

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
            id=__application_id__,
            icon_name=__application_name__,
            category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_menu(self.app.menu)

    def update(self, percents: List[float], tooltip: str):
        svg = draw_pie_chart_svg(percents)
        # Save the temporary directory to an instance variable so that it's not
        # garbage-collected and deleted.
        self.icon_temp_dir = write_temp_file(
            svg,
            filename=__application_name__ + '.svg',
            prefix=__application_id__ + '-',
        )
        self._indicator.set_icon_theme_path(self.icon_temp_dir.name)
        logger.info(
            'Set icon %s/%s',
            self._indicator.get_icon_theme_path(),
            self._indicator.get_icon()
        )
        self._indicator.set_label(tooltip, tooltip)

    def destroy(self):
        self._indicator.show(False)
