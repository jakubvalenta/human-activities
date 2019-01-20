import logging
from functools import partial
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional

import gi
from PIL import Image

from lidske_aktivity.config import TNamedDirs

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


def create_button(callback: Callable,
                  label: Optional[str] = None,
                  stock_id: Optional[str] = None) -> Gtk.Button:
    if label:
        button = Gtk.Button.new_with_label(label)
    else:
        button = Gtk.Button.new_from_stock(stock_id)
    button.connect('clicked', partial(on_button_clicked, callback=callback))
    return button


def on_button_clicked(button: Gtk.Button, callback: Callable):
    callback()


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
        radio_button.connect(
            'toggled',
            partial(on_radio_toggled, callback=callback),
            radio_config.value
        )
        radio_button.set_active(radio_config.value == active_value)
        radio_buttons[radio_config.value] = radio_button
    return radio_buttons


def on_radio_toggled(radio_button: Gtk.RadioButton,
                     value: str,
                     callback: Callable):
    callback(value)


def create_entry(value: str, callback: Callable) -> Gtk.Entry:
    entry = Gtk.Entry()
    if value:
        entry.set_text(value)
    entry.connect('changed', partial(on_entry_changed, callback=callback))
    return entry


def on_entry_changed(entry: Gtk.Entry, callback: Callable):
    callback(entry.get_text())


def create_file_chooser_button(
        value: Optional[str],
        callback: Callable[[str], None]) -> Gtk.FileChooserButton:
    button = Gtk.FileChooserButton.new(
        'Please choose a directory',
        Gtk.FileChooserAction.SELECT_FOLDER
    )
    if value:
        button.set_filename(value)
    button.connect('file_set', partial(on_file_set, callback=callback))
    return button


def on_file_set(button: Gtk.FileChooserButton, callback: Callable):
    callback(button.get_filename())


def image_to_pixbuf(image: Image) -> GdkPixbuf:
    loader = GdkPixbuf.PixbufLoader.new_with_type('png')
    image.save(loader, format='PNG')
    pixbuf = loader.get_pixbuf()
    loader.close()
    return pixbuf


def call_tick(func: Callable):
    GLib.idle_add(func)


class RootPathForm(Gtk.Box):
    _root_path: str
    _parent: Gtk.Window

    def __init__(self,
                 root_path: str,
                 on_change: Callable[[str], None],
                 parent: Gtk.Window):
        self._root_path = root_path
        self._on_change = on_change
        self._parent = parent
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._init_entry()

    def _init_entry(self):
        button = create_file_chooser_button(
            value=self._root_path or None,
            callback=self._on_path_changed
        )
        button.set_hexpand(True)
        box_add(self, button)

    def _on_path_changed(self, path: str):
        self._on_change(path)


class NamedDir(NamedTuple):
    path: str = ''
    name: str = ''


class NamedDirsForm(Gtk.Grid):
    _named_dirs_list: List[NamedDir]

    def __init__(self,
                 named_dirs: TNamedDirs,
                 on_change: Callable[[TNamedDirs], None],
                 parent: Gtk.Window):
        self._named_dirs_list = [
            NamedDir(path, name)
            for path, name in named_dirs.items()
        ]
        self._on_change = on_change
        self._parent = parent
        super().__init__()
        self.set_column_spacing(10)
        self.set_row_spacing(10)
        self._init_entries()

    def _init_entries(self):
        for i, named_dir in enumerate(self._named_dirs_list):
            name_entry = create_entry(
                value=named_dir.name or '',
                callback=partial(self._on_name_changed, i)
            )
            name_entry.set_hexpand(True)
            self.attach(name_entry, left=0, top=i, width=2, height=1)
            choose_button = create_file_chooser_button(
                value=named_dir.path or None,
                callback=partial(self._on_path_changed, i),
            )
            self.attach(choose_button, left=2, top=i, width=2, height=1)
            remove_button = create_button(
                stock_id=Gtk.STOCK_REMOVE,
                callback=partial(self._on_remove_clicked, i),
            )
            self.attach(remove_button, left=4, top=i, width=1, height=1)
        add_button = create_button(
            stock_id=Gtk.STOCK_ADD,
            callback=self._on_add_clicked
        )
        self.attach(
            add_button,
            left=4,
            top=len(self._named_dirs_list),
            width=1,
            height=1
        )
        self.show_all()

    def _clear(self):
        for row in self.get_children():
            self.remove(row)

    def _on_name_changed(self, i: int, name: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(name=name)
        self._on_change(self._named_dirs)

    def _on_path_changed(self, i: int, path: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(path=path)
        self._on_change(self._named_dirs)

    def _on_remove_clicked(self, i: int):
        del self._named_dirs_list[i]
        self._on_change(self._named_dirs)
        self._clear()
        self._init_entries()

    def _on_add_clicked(self):
        new_named_dir = NamedDir()
        self._named_dirs_list.append(new_named_dir)
        self._on_change(self._named_dirs)
        self._clear()
        self._init_entries()

    @property
    def _named_dirs(self) -> TNamedDirs:
        return {
            named_dir.path: named_dir.name
            for named_dir in self._named_dirs_list
            if named_dir.path and named_dir.name
        }
