from typing import Callable, Dict

from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from lidske_aktivity import texts
from lidske_aktivity.config import (
    MODE_NAMED_DIRS,
    MODE_ROOT_PATH,
    MODES,
    UNITS,
    Config,
)
from lidske_aktivity.qt.lib import (
    NamedDirsForm,
    RadioConfig,
    RootPathForm,
    TNamedDirs,
    create_label,
    create_layout,
    create_radio_group,
    create_spin_box,
)


class Settings(QDialog):
    config: Config
    _layout: QVBoxLayout
    _unit_radios: Dict[str, QRadioButton]
    _threshold_days_ago_entry: Dict[str, QSpinBox]
    _mode_radios: Dict[str, QRadioButton]
    _root_path_form: RootPathForm
    _named_dirs_form: NamedDirsForm

    def __init__(
        self, config: Config, on_accept: Callable, ui_app: QApplication
    ):
        self._config = config
        self._on_accept = on_accept
        self._ui_app = ui_app
        super().__init__()
        self._init_window()
        self._create_widgets()
        self._add_widgets()
        self._init_dialog_buttons()
        self._show()

    def _init_window(self):
        self.setWindowTitle(texts.SETTINGS_TITLE)
        self._layout = create_layout()
        self.setLayout(self._layout)

    def _init_dialog_buttons(self):
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def _create_widgets(self):
        self._create_unit_radios()
        self._threshold_days_ago_entry = create_spin_box(
            self,
            value=self._config.threshold_days_ago,
            callback=self._on_threshold_days_ago_changed,
        )
        self._root_path_form = RootPathForm(
            self._config.root_path, self._on_root_path_change, parent=self
        )
        self._named_dirs_form = NamedDirsForm(
            self._ui_app,
            self._config.named_dirs,
            self._on_named_dirs_change,
            parent=self,
        )
        self._create_mode_radios()

    def _add_widgets(self):
        label = create_label(self, texts.SETTINGS_UNIT)
        self._layout.addWidget(label)
        for radio in self._unit_radios.values():
            self._layout.addWidget(radio)
        label = create_label(self, texts.SETTINGS_THRESHOLD_DAYS_OLD)
        self._layout.addWidget(label)
        self._layout.addWidget(self._threshold_days_ago_entry)
        label = create_label(self, texts.SETTINGS_MODE)
        self._layout.addWidget(label)
        self._layout.addWidget(self._mode_radios[MODE_ROOT_PATH])
        self._layout.addLayout(self._root_path_form)
        self._layout.addWidget(self._mode_radios[MODE_NAMED_DIRS])
        self._layout.addLayout(self._named_dirs_form)
        self._toggle_forms()

    def _create_unit_radios(self):
        radio_configs = [
            RadioConfig(value, label) for value, label in UNITS.items()
        ]
        self._unit_radios = create_radio_group(
            self,
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
            self,
            radio_configs,
            active_value=self._config.mode,
            callback=self._on_mode_radio_toggled,
        )

    def _toggle_forms(self):
        self._root_path_form.toggle(self._config.mode == MODE_ROOT_PATH)
        self._named_dirs_form.toggle(self._config.mode == MODE_NAMED_DIRS)

    def _on_mode_radio_toggled(self, mode: str):
        self._config.mode = mode
        self._toggle_forms()

    def _on_root_path_change(self, root_path: str):
        self._config.root_path = root_path

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _show(self):
        if self.exec_():
            self._on_accept(self._config)
