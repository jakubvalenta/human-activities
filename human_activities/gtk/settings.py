from typing import Callable, Dict

import gi

from human_activities import texts
from human_activities.config import (
    MODE_NAMED_DIRS,
    MODE_ROOT_PATH,
    MODES,
    UNITS,
    Config,
    NamedDirs,
)
from human_activities.gtk.lib import (
    NamedDirsForm,
    RadioConfig,
    RootPathForm,
    box_add,
    create_label,
    create_radio_group,
    create_spin_button,
)

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk  # noqa:E402  # isort:skip


class Settings(Gtk.Dialog):
    title = texts.SETTINGS_TITLE

    _config: Config
    _box: Gtk.Box
    _unit_radios: Dict[str, Gtk.RadioButton]
    _threshold_days_ago_entry: Dict[str, Gtk.Entry]
    _mode_radios: Dict[str, Gtk.RadioButton]
    _root_path_form: RootPathForm
    _named_dirs_form: NamedDirsForm

    def __init__(
        self, config: Config, on_accept: Callable, parent: Gtk.Window
    ):
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
                Gtk.ResponseType.OK,
            ),
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
        self._create_unit_radios()
        self._threshold_days_ago_entry = create_spin_button(
            value=self._config.threshold_days_ago,
            callback=self._on_threshold_days_ago_changed,
        )
        self._root_path_form = RootPathForm(
            self._config.root_path, self._on_root_path_change, parent=self
        )
        self._named_dirs_form = NamedDirsForm(
            self._config.named_dirs, self._on_named_dirs_change, parent=self
        )
        # Mode radios must be created after the forms, because the radio
        # callback immediately tries to toggle the forms.
        self._create_mode_radios()

    def _add_widgets(self):
        widgets = (
            [create_label(texts.SETTINGS_UNIT)]
            + list(self._unit_radios.values())
            + [
                create_label(texts.SETTINGS_THRESHOLD_DAYS_OLD),
                self._threshold_days_ago_entry,
                create_label(texts.SETTINGS_MODE),
                self._mode_radios[MODE_ROOT_PATH],
                self._root_path_form,
                self._mode_radios[MODE_NAMED_DIRS],
                self._named_dirs_form,
            ]
        )
        for widget in widgets:
            box_add(self._box, widget, expand=False)

    def _create_unit_radios(self):
        radio_configs = [
            RadioConfig(value, label) for value, label in UNITS.items()
        ]
        self._unit_radios = create_radio_group(
            radio_configs,
            active_value=self._config.unit,
            callback=self._on_unit_radio_toggled,
        )

    def _on_unit_radio_toggled(self, unit: str):
        self._config.unit = unit

    def _on_threshold_days_ago_changed(self, threshold_days_ago: int):
        self._config.threshold_days_ago = threshold_days_ago

    def _create_mode_radios(self):
        radio_configs = [
            RadioConfig(value, label) for value, label in MODES.items()
        ]
        self._mode_radios = create_radio_group(
            radio_configs,
            active_value=self._config.mode,
            callback=self._on_mode_radio_toggled,
        )

    def _on_mode_radio_toggled(self, mode: str):
        self._config.mode = mode
        self._root_path_form.set_sensitive(self._config.mode == MODE_ROOT_PATH)
        self._named_dirs_form.set_sensitive(
            self._config.mode == MODE_NAMED_DIRS
        )

    def _on_root_path_change(self, root_path: str):
        self._config.root_path = root_path

    def _on_named_dirs_change(self, named_dirs: NamedDirs):
        self._config.named_dirs = named_dirs

    def _show(self):
        response = self.run()
        if response == Gtk.ResponseType.OK:
            self._on_accept(self._config)
        self.destroy()
