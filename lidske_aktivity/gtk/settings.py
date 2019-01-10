from pathlib import Path
from typing import Callable, Dict, List

import gi

from lidske_aktivity.config import (
    MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, MODES, Config, TNamedDirs,
)
from lidske_aktivity.gtk.lib import (
    CustomDirsForm, NamedDirsForm, RadioConfig, RootPathForm, box_add,
    create_box, create_label, create_radio_group,
)

gi.require_version('Gtk', '3.0')

from gi.repository import GdkPixbuf, Gtk, GLib  # noqa:E402  # isort:skip


class Settings(Gtk.Dialog):
    title = 'Lidské aktivity advanced settings'

    _config: Config
    _box: Gtk.Box
    _mode_radios: Dict[str, Gtk.RadioButton]

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
        self._init_window()
        self._init_content()
        self._show()

    def _init_window(self):
        content_area = self.get_content_area()
        self._box = create_box(spacing=5, homogeneous=False)
        box_add(content_area, self._box, padding=10)

    def _init_content(self):
        self._create_mode_radios()
        self._add_mode_radio(MODE_HOME)
        self._add_mode_radio(MODE_PATH)
        self._init_root_path_form()
        self._add_mode_radio(MODE_CUSTOM)
        self._init_custom_dirs_form()
        self._add_mode_radio(MODE_NAMED)
        self._init_named_dirs_form()
        self._toggle_controls()

    def _create_mode_radios(self):
        label = create_label('Scan mode')
        box_add(self._box, label)
        radio_configs = [
            RadioConfig(value, label)
            for value, label in MODES.items()
        ]
        self._mode_radios = create_radio_group(
            radio_configs,
            active_value=self._config.mode,
            callback=self._on_mode_radio
        )

    def _on_mode_radio(self, event):
        for mode, radio in self._mode_radios.items():
            if radio.GetValue():
                self._config.mode = mode
        self._toggle_controls()

    def _add_mode_radio(self, mode: str):
        box_add(self._box, self._mode_radios[mode])

    def _init_root_path_form(self):
        self._root_path_form = RootPathForm(
            self._config.root_path,
            on_change=self._on_root_path_change
        )
        box_add(self._box, self._root_path_form)

    def _on_root_path_change(self, root_path: Path):
        self._config.root_path = root_path

    def _init_custom_dirs_form(self):
        self._custom_dirs_form = CustomDirsForm(
            self._config.custom_dirs,
            on_change=self._on_custom_dirs_change
        )
        box_add(self._box, self._custom_dirs_form)

    def _on_custom_dirs_change(self, custom_dirs: List[Path]):
        self._config.custom_dirs = custom_dirs

    def _init_named_dirs_form(self):
        self._named_dirs_form = NamedDirsForm(
            self._config.named_dirs,
            on_change=self._on_named_dirs_change
        )
        box_add(self._box, self._named_dirs_form)

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _toggle_controls(self):
        self._root_path_form.set_sensitive(
            self._config.mode == MODE_PATH
        )
        self._custom_dirs_form.set_sensitive(
            self._config.mode == MODE_CUSTOM
        )
        self._named_dirs_form.set_sensitive(
            self._config.mode == MODE_NAMED
        )

    def _show(self):
        response = self.run()
        if response == Gtk.ResponseType.OK:
            self._on_accept(self._config)
        self.destroy()
