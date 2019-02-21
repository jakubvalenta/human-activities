from typing import Callable, Dict

from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
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
    NamedDirs,
    NamedDirsForm,
    RadioConfig,
    RootPathForm,
    add_layout_items,
    create_group_box,
    create_layout,
    create_radio_group,
    create_spin_box,
    toggle_layout_widgets,
)


class Settings(QDialog):
    config: Config
    _ui_app: QApplication
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
        widgets = [
            self._create_unit_box(),
            self._create_threshold_box(),
            self._create_mode_box(),
            self._create_dialog_buttons(),
        ]
        add_layout_items(self._layout, widgets)
        self._show()

    def _init_window(self):
        self.setWindowTitle(texts.SETTINGS_TITLE)
        self._layout = create_layout()
        self.setLayout(self._layout)

    def _create_unit_box(self) -> QWidget:
        box = create_group_box(texts.SETTINGS_UNIT, self)
        radio_configs = [
            RadioConfig(value, label) for value, label in UNITS.items()
        ]
        self._unit_radios = create_radio_group(
            box,
            radio_configs,
            active_value=self._config.unit,
            callback=self._on_unit_radio_toggled,
        )
        add_layout_items(box.layout(), self._unit_radios.values())
        return box

    def _on_unit_radio_toggled(self, unit: str):
        self._config.unit = unit

    def _create_threshold_box(self) -> QWidget:
        box = create_group_box(texts.SETTINGS_THRESHOLD_DAYS_OLD, self)
        self._threshold_days_ago_entry = create_spin_box(
            self,
            value=self._config.threshold_days_ago,
            callback=self._on_threshold_days_ago_changed,
        )
        add_layout_items(box.layout(), [self._threshold_days_ago_entry])
        return box

    def _on_threshold_days_ago_changed(self, threshold_days_ago: int):
        self._config.threshold_days_ago = threshold_days_ago

    def _create_mode_box(self) -> QWidget:
        box = create_group_box(texts.SETTINGS_MODE, self)
        self._root_path_form = RootPathForm(
            self._ui_app,
            self._config.root_path,
            self._on_root_path_change,
            parent=box,
        )
        self._named_dirs_form = NamedDirsForm(
            self._ui_app,
            self._config.named_dirs,
            self._on_named_dirs_change,
            parent=box,
        )
        # Mode radios must be created after the forms, because the radio
        # callback immediately tries to toggle the forms.
        radio_configs = [
            RadioConfig(value, label) for value, label in MODES.items()
        ]
        self._mode_radios = create_radio_group(
            box,
            radio_configs,
            active_value=self._config.mode,
            callback=self._on_mode_radio_toggled,
        )
        add_layout_items(
            box.layout(),
            [
                self._mode_radios[MODE_ROOT_PATH],
                self._root_path_form,
                self._mode_radios[MODE_NAMED_DIRS],
                self._named_dirs_form,
            ],
        )
        return box

    def _on_mode_radio_toggled(self, mode: str):
        self._config.mode = mode
        self._toggle_forms()

    def _on_root_path_change(self, root_path: str):
        self._config.root_path = root_path

    def _on_named_dirs_change(self, named_dirs: NamedDirs):
        self._config.named_dirs = named_dirs

    def _toggle_forms(self):
        toggle_layout_widgets(
            self._root_path_form, self._config.mode == MODE_ROOT_PATH
        )
        toggle_layout_widgets(
            self._named_dirs_form, self._config.mode == MODE_NAMED_DIRS
        )

    def _create_dialog_buttons(self) -> QWidget:
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        return button_box

    def _show(self):
        if self.exec_():
            self._on_accept(self._config)
