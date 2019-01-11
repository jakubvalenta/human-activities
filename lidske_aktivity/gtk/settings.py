from pathlib import Path
from typing import Callable, Dict, List

import gi

from lidske_aktivity.config import (
    MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, MODES, Config, TNamedDirs,
)
from lidske_aktivity.gtk.lib import (
    CustomDirsForm, NamedDirsForm, RadioConfig, RootPathForm, box_add,
    create_label, create_radio_group,
)

gi.require_version('Gtk', '3.0')

from gi.repository import GdkPixbuf, Gtk, GLib  # noqa:E402  # isort:skip


class Settings(Gtk.Dialog):
    title = 'Lidské aktivity advanced settings'

    _config: Config
    _box: Gtk.Box
    _mode_radios: Dict[str, Gtk.RadioButton]
    _root_path_form: RootPathForm
    _custom_dirs_form: CustomDirsForm
    _named_dirs_form: NamedDirsForm

    def __init__(self,
                 config: Config,
                 on_accept: Callable,
                 parent: Gtk.Window):
        self._config = config
        self._on_accept = on_accept
        super().__init__(
            self.title,
            parent,
            0,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK
            )
        )
        self.set_default_size(500, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self._init_window()
        self._create_widgets()
        self._add_widgets()
        self._show()

    def _init_window(self):
        self._box = self.get_content_area()
        self._box.set_homogeneous(False)
        self._box.set_border_width(10)
        self._box.set_spacing(10)

    def _create_widgets(self):
        self._root_path_form = RootPathForm(
            self._config.root_path,
            self._on_root_path_change,
            parent=self
        )
        self._custom_dirs_form = CustomDirsForm(
            self._config.custom_dirs,
            self._on_custom_dirs_change,
            parent=self
        )
        self._named_dirs_form = NamedDirsForm(
            self._config.named_dirs,
            self._on_named_dirs_change,
            parent=self
        )
        self._create_mode_radios()

    def _add_widgets(self):
        for widget in (
                create_label('Scan mode'),
                self._mode_radios[MODE_HOME],
                self._mode_radios[MODE_PATH],
                self._root_path_form,
                self._mode_radios[MODE_CUSTOM],
                self._custom_dirs_form,
                self._mode_radios[MODE_NAMED],
                self._named_dirs_form,
        ):
            box_add(self._box, widget, expand=False)

    def _create_mode_radios(self):
        radio_configs = [
            RadioConfig(value, label)
            for value, label in MODES.items()
        ]
        self._mode_radios = create_radio_group(
            radio_configs,
            active_value=self._config.mode,
            callback=self._on_mode_radio_toggled
        )

    def _on_mode_radio_toggled(self, mode: str):
        self._config.mode = mode
        self._root_path_form.set_sensitive(self._config.mode == MODE_PATH)
        self._custom_dirs_form.set_sensitive(self._config.mode == MODE_CUSTOM)
        self._named_dirs_form.set_sensitive(self._config.mode == MODE_NAMED)

    def _on_root_path_change(self, root_path: Path):
        self._config.root_path = root_path

    def _on_custom_dirs_change(self, custom_dirs: List[Path]):
        self._config.custom_dirs = custom_dirs

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _show(self):
        response = self.run()
        if response == Gtk.ResponseType.OK:
            self._on_accept(self._config)
        self.destroy()
