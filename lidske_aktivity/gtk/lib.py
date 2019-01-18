import logging
from functools import partial
from pathlib import Path
from typing import (
    Callable, Dict, Iterable, Iterator, List, NamedTuple, Optional,
)

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


def create_button(label: str, callback: Callable):
    button = Gtk.Button.new_with_label(label)
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


def choose_dir(parent: Gtk.Window, callback: Callable[[str], None]):
    dialog = Gtk.FileChooserDialog(
        'Please choose a directory',
        parent,
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


class RootPathForm(Gtk.Box):
    _root_path: Path
    _entry: Gtk.Entry
    _parent: Gtk.Window

    def __init__(self,
                 root_path: Path,
                 on_change: Callable[[Path], None],
                 parent: Gtk.Window):
        self._root_path = root_path
        self._on_change = on_change
        self._parent = parent
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._entry = self._init_entry()

    def _init_entry(self) -> Gtk.Entry:
        entry = create_entry(
            value=str(self._root_path) if self._root_path else '',
            callback=self._on_text
        )
        entry.set_hexpand(True)
        box_add(self, entry)
        button = create_button('Choose', self._on_button)
        box_add(self, button, expand=False)
        return entry

    def _on_text(self, path_str: str):
        self._on_change(Path(path_str))

    def _on_button(self):
        def callback(path_str: str):
            self._on_change(Path(path_str))
            self._entry.set_text(path_str)

        choose_dir(self._parent, callback)


class NamedDir(NamedTuple):
    path: Path
    name: str


class NamedDirsForm(Gtk.Grid):
    _named_dirs_list: List[NamedDir]
    _path_entries: List[Gtk.Entry]

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
        self._path_entries = list(self._init_entries())

    def _init_entries(self) -> Iterator[Gtk.Entry]:
        for i, named_dir in enumerate(self._named_dirs_list):
            entry_name = create_entry(
                value=named_dir.name or '',
                callback=partial(self._on_name_text, i)
            )
            entry_name.set_hexpand(True)
            self.attach(entry_name, left=0, top=i, width=1, height=1)
            entry_path = create_entry(
                value=str(named_dir.path) or '',
                callback=partial(self._on_path_text, i)
            )
            entry_path.set_hexpand(True)
            self.attach(entry_path, left=1, top=i, width=1, height=1)
            button = create_button(
                'Choose',
                partial(self._on_path_button, i)
            )
            self.attach(button, left=2, top=i, width=1, height=1)
            yield entry_path

    def _on_name_text(self, i: int, name: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(name=name)
        self._on_change(self._named_dirs)

    def _on_path_text(self, i: int, path_str: str):
        named_dir = self._named_dirs_list[i]
        self._named_dirs_list[i] = named_dir._replace(path=Path(path_str))
        self._on_change(self._named_dirs)

    def _on_path_button(self, i: int):
        def callback(path_str: str):
            named_dir = self._named_dirs_list[i]
            self._named_dirs_list[i] = named_dir._replace(path=Path(path_str))
            self._on_change(self._named_dirs)
            self._path_entries[i].set_text(path_str)

        choose_dir(self._parent, callback)

    @property
    def _named_dirs(self) -> TNamedDirs:
        return {
            named_dir.path: named_dir.name
            for named_dir in self._named_dirs_list
        }
