import logging
from typing import Callable

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


def create_menu_item(menu: Gtk.Menu,
                     label: str,
                     callback: Callable = None) -> None:
    menu_item = Gtk.MenuItem()
    menu_item.set_label(label)
    if callback:
        menu_item.connect('activate', callback)
    else:
        menu_item.set_sensitive(False)
    menu.append(menu_item)


def call_tick(func: Callable):
    GLib.idle_add(func)
