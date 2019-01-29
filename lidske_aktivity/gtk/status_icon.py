import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, Iterator, Optional

import gi

from lidske_aktivity import __application_id__, __application_name__
from lidske_aktivity.gtk.lib import create_box, image_to_pixbuf
from lidske_aktivity.icon import (
    calc_icon_hash, draw_pie_chart_png, draw_pie_chart_svg,
)
from lidske_aktivity.model import DirectoryViews

gi.require_version('AppIndicator3', '0.1')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')

from gi.repository import AppIndicator3, GdkPixbuf, Gtk  # noqa:E402  # isort:skip

if TYPE_CHECKING:
    from lidske_aktivity.app import Application

logger = logging.getLogger(__name__)


def create_menu_item(
        label: str,
        callback: Optional[Callable] = None,
        tooltip: Optional[str] = None,
        icon_name: Optional[str] = None,
        icon_pixbuf: Optional[GdkPixbuf.Pixbuf] = None) -> Gtk.MenuItem:
    menu_item = Gtk.MenuItem()
    if icon_name:
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
    elif icon_pixbuf:
        image = Gtk.Image.new_from_pixbuf(icon_pixbuf)
    else:
        image = None
    if image:
        hbox = create_box(Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.add(image)
        label_widget = Gtk.Label(label)
        hbox.add(label_widget)
        menu_item.add(hbox)
    else:
        menu_item.set_label(label)
    if tooltip:
        menu_item.set_tooltip_text(tooltip)
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
    _indicator: AppIndicator3.Indicator

    # The directory is deleted as soon as this variable is garbage-collected.
    _icon_temp_dir: tempfile.TemporaryDirectory

    def __init__(self, app: 'Application'):
        self.app = app
        self._indicator = create_indicator()
        self._init_menu()

    def _create_menu_items(
            self,
            directory_views: Optional[DirectoryViews]
    ) -> Iterator[Gtk.MenuItem]:
        # TODO: Limit the maximum number of items shown.
        if directory_views:
            for i, directory_view in enumerate(directory_views.values()):
                _, icon_size, _ = Gtk.IconSize.lookup(Gtk.IconSize.MENU)
                icon_image = draw_pie_chart_png(
                    icon_size,
                    directory_views.fractions,
                    directory_views.get_colors_with_one_highlighted(i)
                )
                icon_pixbuf = image_to_pixbuf(icon_image)
                yield create_menu_item(
                    directory_view.text,
                    tooltip=directory_view.tooltip,
                    icon_pixbuf=icon_pixbuf
                )
        else:
            yield create_menu_item('No directories configured')
        yield Gtk.SeparatorMenuItem()
        yield create_menu_item(
            'Setup',
            lambda event: self.app.show_setup()
        )
        yield create_menu_item(
            'Advanced configuration',
            lambda event: self.app.show_settings()
        )
        yield create_menu_item(
            'About',
            lambda event: self.app.show_about(),
            icon_name='help-about'
        )
        yield create_menu_item(
            'Quit',
            lambda event: self.app.quit(),
            icon_name='application-exit'
        )

    def _init_menu(self, directory_views: Optional[DirectoryViews] = None):
        menu = Gtk.Menu()
        for menu_item in self._create_menu_items(directory_views):
            menu.append(menu_item)
        menu.show_all()
        self._indicator.set_menu(menu)

    def update(self, directory_views: DirectoryViews):
        svg = draw_pie_chart_svg(directory_views.fractions)
        icon_hash = calc_icon_hash(directory_views.fractions)
        icon_temp_dir = write_temp_file(
            svg,
            filename=icon_hash + '.svg',
            prefix=__application_id__ + '-',
        )
        set_indicator_icon(
            self._indicator,
            icon_theme_path=icon_temp_dir.name,
            icon_name=icon_hash,
            tooltip=directory_views.tooltip
        )
        self._icon_temp_dir = icon_temp_dir
        self._init_menu(directory_views)

    def destroy(self):
        self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
