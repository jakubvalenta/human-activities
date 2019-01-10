import logging
from typing import Callable

import gi
from PIL import Image

gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GdkPixbuf, Gtk, GLib  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


def create_box(orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL,
               *args,
               **kwargs) -> Gtk.Box:
    return Gtk.Box(orientation, *args, **kwargs)


def box_add(box: Gtk.Box, widget: Gtk.Widget):
    box.pack_start(widget, True, True, 0)
    box.show_all()


def create_label(text: str) -> Gtk.Label:
    return Gtk.Label(text)


def create_button(label: str, callback: Callable):
    button = Gtk.Button.new_with_label(label)
    button.connect('clicked', callback)
    return button


def image_to_pixbuf(image: Image) -> GdkPixbuf:
    loader = GdkPixbuf.PixbufLoader.new_with_type('png')
    image.save(loader, format='PNG')
    pixbuf = loader.get_pixbuf()
    loader.close()
    return pixbuf


def call_tick(func: Callable):
    GLib.idle_add(func)
