import logging
from typing import (
    Callable, Dict, Iterable, Iterator, List, NamedTuple, Optional,
)

import gi
from PIL import Image

gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GdkPixbuf, Gtk, GLib  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


def create_box(orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL,
               homogeneous: bool = True,
               **kwargs) -> Gtk.Box:
    box = Gtk.Box(orientation=orientation, **kwargs)
    if not homogeneous:
        box.set_homogeneous(homogeneous)
    return box


def box_add(box: Gtk.Box,
            widget: Gtk.Widget,
            expand: bool = True,
            fill: bool = True,
            padding: int = 0):
    box.pack_start(widget, expand, fill, padding)
    box.show_all()


def create_label(text: str) -> Gtk.Label:
    label = Gtk.Label(text)
    label.set_justify(Gtk.Justification.LEFT)
    label.set_xalign(0)
    return label


def create_button(label: str, callback: Callable):
    button = Gtk.Button.new_with_label(label)
    button.connect('clicked', callback)
    return button


class RadioConfig(NamedTuple):
    value: str
    label: str
    tooltip: Optional[str] = None
    mode: bool = False


def create_radio_group(
        radio_configs: Iterable[RadioConfig],
        active_value: str,
        callback: Callable,
        use_toggle_buttons: bool = False) -> Dict[str, Gtk.RadioButton]:
    radio_buttons = {}
    group = None
    for radio_config in radio_configs:
        radio_button = Gtk.RadioButton.new_with_label_from_widget(
            group,
            radio_config.label
        )
        if use_toggle_buttons:
            radio_button.set_mode(False)
        if radio_config.tooltip:
            radio_button.set_tooltip_text(radio_config.tooltip)
        if not group:
            group = radio_button
        radio_button.connect('toggled', callback, radio_config.value)
        radio_button.set_active(radio_config.value == active_value)
        radio_buttons[radio_config.value] = radio_button
    return radio_buttons


def create_entry(value: str,
                 callback: Callable) -> Gtk.Entry:
    entry = Gtk.Entry()
    if value:
        entry.set_text(value)
    entry.connect('changed', callback)
    return entry


def choose_dir(parent_window: Gtk.Window, callback: Callable[[str], None]):
    dialog = Gtk.FileChooserDialog(
        'Please choose a directory',
        parent_window,
        Gtk.FileChooserAction.SELECT_FOLDER,
        (
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            'Select',
            Gtk.ResponseType.OK
        )
    )
    dialog.set_default_size(800, 400)
    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        path = dialog.get_filename()
        callback(path)
    dialog.destroy()


def image_to_pixbuf(image: Image) -> GdkPixbuf:
    loader = GdkPixbuf.PixbufLoader.new_with_type('png')
    image.save(loader, format='PNG')
    pixbuf = loader.get_pixbuf()
    loader.close()
    return pixbuf


def call_tick(func: Callable):
    GLib.idle_add(func)
