import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Iterator, List, Tuple

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


def create_indicator(
        menu: Gtk.Menu,
        secondary_target: Gtk.MenuItem) -> AppIndicator3.Indicator:
    indicator = AppIndicator3.Indicator.new(
        id=__application_id__,
        icon_name=__application_name__,
        category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu)
    indicator.set_secondary_activate_target(secondary_target)
    return indicator


def write_temp_file(lines: Iterable[str],
                    filename: str,
                    **kwargs) -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory(**kwargs)
    with (Path(temp_dir.name) / filename).open('w') as f:
        f.writelines(lines)
    return temp_dir


def set_indicator_dynamic_icon(indicator: AppIndicator3.Indicator,
                               svg: Iterator[str],
                               tooltip: str) -> tempfile.TemporaryDirectory:
    """Set an AppIndicator icon from a generated SVG file.

    Return a reference to the temporary directory in which the icon was saved.
    This reference should be stored in a variable, so that it's not
    garbage-collected and the icon deleted.
    """
    icon_temp_dir = write_temp_file(
        svg,
        filename=__application_name__ + '.svg',
        prefix=__application_id__ + '-',
    )
    indicator.set_icon_full(__application_name__, tooltip)
    indicator.set_icon_theme_path(icon_temp_dir.name)
    logger.info(
        'Set icon %s/%s',
        indicator.get_icon_theme_path(),
        indicator.get_icon()
    )
    return icon_temp_dir


class StatusIcon():
    app: 'Application'
    indicator: AppIndicator3.Indicator
    icon_temp_dir: tempfile.TemporaryDirectory

    def __init__(self, app: 'Application'):
        self.app = app
        menu, secondary_target = self._create_menu()
        self.indicator = create_indicator(menu, secondary_target)

    def _create_menu(self) -> Tuple[Gtk.Menu, Gtk.MenuItem]:
        menu = Gtk.Menu()
        secondary_target = create_menu_item(
            menu,
            'Show',
            lambda event: self.app.show_menu(0, 0)
        )
        create_menu_item(
            menu,
            'Setup',
            lambda event: self.app.show_setup()
        )
        create_menu_item(
            menu,
            'Advanced configuration',
            lambda event: self.app.show_settings()
        )
        create_menu_item(
            menu,
            'Quit',
            lambda event: self.app.quit()
        )
        menu.show_all()
        return menu, secondary_target

    def update(self, percents: List[float], tooltip: str):
        svg = draw_pie_chart_svg(percents)
        self.icon_temp_dir = set_indicator_dynamic_icon(
            self.indicator,
            svg,
            tooltip
        )

    def destroy(self):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
