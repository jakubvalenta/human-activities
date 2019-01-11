import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, List, Optional

import gi

from lidske_aktivity import __application_id__, __application_name__
from lidske_aktivity.icon import calc_icon_hash, draw_pie_chart_svg

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import AppIndicator3, Gtk  # noqa:E402  # isort:skip

if TYPE_CHECKING:
    from lidske_aktivity.app import Application

logger = logging.getLogger(__name__)


def create_menu_item(label: str,
                     callback: Callable = None,
                     icon: Optional[str] = None) -> Gtk.MenuItem:
    if icon:
        menu_item = Gtk.ImageMenuItem()
        image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
        menu_item.set_image(image)
    else:
        menu_item = Gtk.MenuItem()
    menu_item.set_label(label)
    if callback:
        menu_item.connect('activate', callback)
    else:
        menu_item.set_sensitive(False)
    return menu_item


def create_indicator() -> AppIndicator3.Indicator:
    indicator = AppIndicator3.Indicator.new(
        id=__application_id__,
        icon_name=__application_name__,
        category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    return indicator


def write_temp_file(lines: Iterable[str],
                    filename: str,
                    **kwargs) -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory(**kwargs)
    with (Path(temp_dir.name) / filename).open('w') as f:
        f.writelines(lines)
    return temp_dir


def set_indicator_icon(indicator: AppIndicator3.Indicator,
                       icon_theme_path: str,
                       icon_name: str,
                       tooltip: str):
    indicator.set_icon_full(icon_name, tooltip)
    indicator.set_icon_theme_path(icon_theme_path)
    logger.info(
        'Set icon %s/%s',
        indicator.get_icon_theme_path(),
        indicator.get_icon()
    )


class StatusIcon():
    app: 'Application'
    _menu: Gtk.Menu
    _dynamic_menu_items: List[Gtk.MenuItem]
    _indicator: AppIndicator3.Indicator

    # The directory is deleted as soon as this variable is garbage-collected.
    icon_temp_dir: tempfile.TemporaryDirectory

    def __init__(self, app: 'Application'):
        self.app = app
        self._indicator = create_indicator()
        self._init_menu([])

    def _init_menu(self, texts: List[str]):
        menu = Gtk.Menu()
        secondary_target = create_menu_item(
            'Show',
            lambda event: self.app.show_menu(0, 0),
            icon='lidske-aktivity'
        )
        menu_items = [
            secondary_target,
            Gtk.SeparatorMenuItem(),
        ] + [
            create_menu_item(text) for text in texts
        ] + [
            Gtk.SeparatorMenuItem(),
            create_menu_item(
                'Setup',
                lambda event: self.app.show_setup()
            ),
            create_menu_item(
                'Advanced configuration',
                lambda event: self.app.show_settings()
            ),
            create_menu_item(
                'About',
                lambda event: self.app.show_about(),
                icon='help-about'
            ),
            create_menu_item(
                'Quit',
                lambda event: self.app.quit(),
                icon='application-exit'
            ),
        ]
        for menu_item in menu_items:
            menu.append(menu_item)
        menu.show_all()
        self._indicator.set_menu(menu)
        self._indicator.set_secondary_activate_target(secondary_target)

    def update(self, percents: List[float], texts: List[str]):
        svg = draw_pie_chart_svg(percents)
        icon_hash = calc_icon_hash(percents)
        icon_temp_dir = write_temp_file(
            svg,
            filename=icon_hash + '.svg',
            prefix=__application_id__ + '-',
        )
        tooltip = '\n'.join(texts)
        set_indicator_icon(
            self._indicator,
            icon_theme_path=icon_temp_dir.name,
            icon_name=icon_hash,
            tooltip=tooltip
        )
        self._icon_temp_dir = icon_temp_dir
        self._init_menu(texts)

    def destroy(self):
        self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
