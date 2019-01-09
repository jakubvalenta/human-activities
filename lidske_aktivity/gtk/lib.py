import logging
from typing import Callable

import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, GLib  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


def create_button(label: str, callback: Callable):
    button = Gtk.Button.new_with_label(label)
    button.connect('clicked', callback)
    return button


def call_tick(func: Callable):
    GLib.idle_add(func)
