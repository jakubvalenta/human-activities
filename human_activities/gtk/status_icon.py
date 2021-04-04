import logging
import tempfile
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterator, Optional, Tuple

import gi

from human_activities import (
    __application_id__,
    __application_name__,
    __title__,
    texts,
)
from human_activities.gtk.lib import create_box, image_to_pixbuf
from human_activities.icon import (
    DEFAULT_FRACTIONS,
    calc_icon_hash,
    draw_pie_chart_png,
    draw_pie_chart_svg,
)
from human_activities.l10n import _
from human_activities.model import DirectoryViews

gi.require_version('AppIndicator3', '0.1')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')

from gi.repository import (  # noqa:E402  # isort:skip
    AppIndicator3,
    GLib,
    GdkPixbuf,
    Gtk,
)

if TYPE_CHECKING:
    from human_activities.app import Application

logger = logging.getLogger(__name__)


def create_menu_item(
    label: str,
    callback: Optional[Callable] = None,
    tooltip: Optional[str] = None,
    icon_name: Optional[str] = None,
    icon_pixbuf: Optional[GdkPixbuf.Pixbuf] = None,
    markup: Optional[str] = None,
) -> Gtk.MenuItem:
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
    if markup:
        label_widget = menu_item.get_child()
        label_widget.set_markup(markup)
    if callback:
        menu_item.connect('activate', callback)
    else:
        menu_item.set_sensitive(False)
    return menu_item


def create_indicator() -> AppIndicator3.Indicator:
    indicator = AppIndicator3.Indicator.new(
        id=__application_id__,
        icon_name=__application_name__,
        category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    return indicator


def write_temp_file(
    svg: str, filename: str, **kwargs
) -> tempfile.TemporaryDirectory:
    temp_dir = tempfile.TemporaryDirectory(**kwargs)
    (Path(temp_dir.name) / filename).write_text(svg)
    return temp_dir


def set_indicator_icon(
    indicator: AppIndicator3.Indicator,
    icon_theme_path: str,
    icon_name: str,
    tooltip: str,
):
    indicator.set_icon_full(icon_name, tooltip)
    indicator.set_icon_theme_path(icon_theme_path)
    logger.info(
        'Set icon %s/%s', indicator.get_icon_theme_path(), indicator.get_icon()
    )


def markup_italic(s: str) -> str:
    return f'<i>{s}</i>'


class StatusIcon:
    app: 'Application'
    _indicator: AppIndicator3.Indicator
    _last_fractions: Optional[Tuple[float, ...]] = None
    # The directory is deleted as soon as this variable is garbage-collected.
    _icon_temp_dir: tempfile.TemporaryDirectory

    def __init__(self, app: 'Application'):
        self.app = app
        self._indicator = create_indicator()
        self._set_icon(DEFAULT_FRACTIONS, __title__)
        self._init_menu()

    def _create_menu_items(
        self, directory_views: Optional[DirectoryViews] = None
    ) -> Iterator[Gtk.MenuItem]:
        if directory_views:
            for i, directory_view in enumerate(directory_views.values()):
                icon_size = Gtk.IconSize.lookup(Gtk.IconSize.MENU)[1]
                icon_image = draw_pie_chart_png(
                    icon_size, directory_views.fractions, highlighted=i
                )
                icon_pixbuf = image_to_pixbuf(icon_image)
                yield create_menu_item(
                    directory_view.text, icon_pixbuf=icon_pixbuf
                )
            if directory_views.configured_dirs.truncated:
                yield create_menu_item(
                    texts.MENU_DIRS_TRUNCATED.format(
                        max_len=directory_views.configured_dirs.max_len
                    )
                )
            if directory_views.threshold_days_ago:
                yield Gtk.SeparatorMenuItem()
                yield create_menu_item(
                    label='',
                    markup=markup_italic(
                        texts.MENU_THRESHOLD_DAYS_AGO.format(
                            days=directory_views.threshold_days_ago
                        )
                    ),
                )
        else:
            yield create_menu_item(texts.MENU_EMPTY)
        yield Gtk.SeparatorMenuItem()
        yield create_menu_item(_('Setup'), lambda event: self.app.show_setup())
        yield create_menu_item(
            _('Advanced configuration'), lambda event: self.app.show_settings()
        )
        yield create_menu_item(
            _('About'),
            lambda event: self.app.show_about(),
            icon_name='help-about',
        )
        yield create_menu_item(
            _('Quit'),
            lambda event: self.app.quit(),
            icon_name='application-exit',
        )

    def _init_menu(self, directory_views: Optional[DirectoryViews] = None):
        menu = Gtk.Menu()
        for menu_item in self._create_menu_items(directory_views):
            menu.append(menu_item)
        menu.show_all()
        self._indicator.set_menu(menu)

    def update(self, directory_views: DirectoryViews):
        GLib.idle_add(partial(self._on_update, directory_views))

    def _on_update(self, directory_views: DirectoryViews):
        self._init_menu(directory_views)
        self._set_icon(directory_views.fractions, directory_views.tooltip)

    def _set_icon(self, fractions: Tuple[float, ...], tooltip: str):
        icon_hash = calc_icon_hash(fractions)
        if self._last_fractions == fractions:
            icon_temp_dir = self._icon_temp_dir
        else:
            svg = draw_pie_chart_svg(fractions)
            icon_temp_dir = write_temp_file(
                svg,
                filename=icon_hash + '.svg',
                prefix=__application_id__ + '-',
            )
            self._last_fractions = fractions
        set_indicator_icon(
            self._indicator,
            icon_theme_path=icon_temp_dir.name,
            icon_name=icon_hash,
            tooltip=tooltip,
        )
        self._icon_temp_dir = icon_temp_dir

    def destroy(self):
        self._indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
