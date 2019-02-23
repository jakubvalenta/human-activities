import logging
from functools import partial
from typing import Callable, Dict, Iterable, NamedTuple, Optional

import gi
from PIL import Image

from human_activities import texts
from human_activities.config import NamedDirs
from human_activities.utils.func import after

gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GdkPixbuf, Gtk  # noqa:E402  # isort:skip

logger = logging.getLogger(__name__)


def create_box(
    orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL,
    homogeneous: bool = True,
    **kwargs,
) -> Gtk.Box:
    box = Gtk.Box(orientation=orientation, **kwargs)
    if not homogeneous:
        box.set_homogeneous(homogeneous)
    return box


def box_add(
    box: Gtk.Box,
    widget: Gtk.Widget,
    expand: bool = True,
    fill: bool = True,
    padding: int = 0,
):
    box.pack_start(widget, expand, fill, padding)
    box.show_all()


def create_label(text: str) -> Gtk.Label:
    label = Gtk.Label(text)
    label.set_justify(Gtk.Justification.LEFT)
    label.set_xalign(0)
    return label


def create_button(
    callback: Callable,
    label: Optional[str] = None,
    stock_id: Optional[str] = None,
) -> Gtk.Button:
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
    use_toggle_buttons: bool = False,
) -> Dict[str, Gtk.RadioButton]:
    radio_buttons = {}
    group = None
    for radio_config in radio_configs:
        radio_button = Gtk.RadioButton.new_with_label_from_widget(
            group, radio_config.label
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
            radio_config.value,
        )
        radio_button.set_active(radio_config.value == active_value)
        radio_buttons[radio_config.value] = radio_button
    return radio_buttons


def on_radio_toggled(
    radio_button: Gtk.RadioButton, value: str, callback: Callable
):
    callback(value)


def create_entry(value: str, callback: Callable) -> Gtk.Entry:
    entry = Gtk.Entry()
    if value:
        entry.set_text(value)
    entry.connect('changed', partial(on_entry_changed, callback=callback))
    return entry


def on_entry_changed(entry: Gtk.Entry, callback: Callable):
    callback(entry.get_text())


def create_spin_button(
    value: int,
    callback: Callable,
    min_val: int = 0,
    max_val: int = 9999,
    step: int = 1,
) -> Gtk.SpinButton:
    spin_button = Gtk.SpinButton.new_with_range(min_val, max_val, step)
    if value:
        spin_button.set_value(value)
    spin_button.connect(
        'value_changed', partial(on_spin_button_changed, callback=callback)
    )
    return spin_button


def on_spin_button_changed(spin_button: Gtk.SpinButton, callback: Callable):
    callback(spin_button.get_value_as_int())


def create_file_chooser_button(
    value: Optional[str], callback: Callable[[str], None]
) -> Gtk.FileChooserButton:
    button = Gtk.FileChooserButton.new(
        texts.FILE_CHOOSER_BUTTON, Gtk.FileChooserAction.SELECT_FOLDER
    )
    if value:
        button.set_filename(value)
    button.connect('file_set', partial(on_file_set, callback=callback))
    return button


def on_file_set(button: Gtk.FileChooserButton, callback: Callable):
    callback(button.get_filename())


def image_to_pixbuf(image: Image.Image) -> GdkPixbuf.Pixbuf:
    loader = GdkPixbuf.PixbufLoader.new_with_type('png')
    image.save(loader, format='PNG')
    pixbuf = loader.get_pixbuf()
    loader.close()
    return pixbuf


class RootPathForm(Gtk.Box):
    _root_path: Optional[str]

    def __init__(
        self,
        root_path: Optional[str],
        on_change: Callable[[str], None],
        parent: Gtk.Window,
    ):
        self._root_path = root_path
        self._on_change = on_change
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._create_widgets()

    def _create_widgets(self):
        button = create_file_chooser_button(
            value=self._root_path or None, callback=self._on_path_changed
        )
        button.set_hexpand(True)
        box_add(self, button)

    def _on_path_changed(self, path: str):
        self._on_change(path)


class NamedDirsForm(Gtk.Box):
    _named_dirs: NamedDirs
    _custom_names_enabled: bool

    def __init__(
        self,
        named_dirs: NamedDirs,
        on_change: Callable[[NamedDirs], None],
        parent: Gtk.Window,
        custom_names_enabled: bool = True,
    ):
        self._named_dirs = named_dirs
        self._on_change = on_change
        self._custom_names_enabled = custom_names_enabled
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_homogeneous(False)
        self._create_widgets()

    def _create_widgets(self):
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        for i, named_dir in enumerate(self._named_dirs):
            left = 0
            if self._custom_names_enabled:
                name_entry = create_entry(
                    value=named_dir.name or '',
                    callback=after(
                        partial(self._named_dirs.set_name, i), self._changed
                    ),
                )
                name_entry.set_hexpand(True)
                grid.attach(name_entry, left=left, top=i, width=2, height=1)
                left += 2
            choose_button = create_file_chooser_button(
                value=named_dir.path or None,
                callback=after(
                    partial(self._named_dirs.set_path, i), self._changed
                ),
            )
            if left == 0:
                choose_button.set_hexpand(True)
            grid.attach(choose_button, left=left, top=i, width=2, height=1)
            left += 2
            remove_button = create_button(
                stock_id=Gtk.STOCK_REMOVE,
                callback=after(
                    partial(self._named_dirs.remove, i),
                    self._recreate,
                    self._changed,
                ),
            )
            grid.attach(remove_button, left=left, top=i, width=1, height=1)
        grid.show_all()
        box_add(self, grid)
        if not self._named_dirs.max_reached:
            # TODO: Make the button not fill the whole box width.
            add_button = create_button(
                stock_id=Gtk.STOCK_ADD,
                callback=after(
                    self._named_dirs.new, self._recreate, self._changed
                ),
            )
            box_add(self, add_button, expand=False)
        else:
            label = create_label(
                texts.SETTINGS_MAX_DIRS_REACHED.format(
                    max_len=self._named_dirs.max_len
                )
            )
            box_add(self, label, expand=False)

    def _changed(self):
        self._on_change(self._named_dirs)

    def _recreate(self):
        for row in self.get_children():
            self.remove(row)
        self._create_widgets()
