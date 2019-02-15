import io
import logging
from functools import partial
from typing import Callable, Dict, Iterable, List, NamedTuple, Optional

from PIL import Image
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from lidske_aktivity.config import TNamedDirs
from lidske_aktivity.texts import _

logger = logging.getLogger(__name__)


def create_layout() -> QVBoxLayout:
    return QVBoxLayout()


def create_label(parent: QWidget, text: str) -> QLabel:
    return QLabel(text, parent)


def create_button(
    parent: QWidget,
    callback: Callable,
    label: Optional[str] = None,
    icon_pixmap: Optional[QPixmap] = None,
) -> QPushButton:
    button = QPushButton(parent)
    if label:
        button.setText(label)
    if icon_pixmap:
        icon = create_icon(icon_pixmap)
        button.setIcon(icon)
    button.clicked.connect(callback)
    return button


class RadioConfig(NamedTuple):
    value: str
    label: str
    tooltip: Optional[str] = None


def create_radio_group(
    parent: QWidget,
    radio_configs: Iterable[RadioConfig],
    active_value: str,
    callback: Callable,
) -> Dict[str, QRadioButton]:
    radio_buttons = {}
    for radio_config in radio_configs:
        radio = QRadioButton(radio_config.label, parent)
        radio.toggled.connect(
            partial(
                on_radio_toggled, value=radio_config.value, callback=callback
            )
        )
        if radio_config.value == active_value:
            radio.setChecked(True)
        radio_buttons[radio_config.value] = radio
    return radio_buttons


def on_radio_toggled(checked: bool, value: str, callback: Callable):
    if checked:
        callback(value)


def create_line_edit(
    parent: QWidget, value: str, callback: Callable
) -> QLineEdit:
    line_edit = QLineEdit(value, parent)
    line_edit.textChanged[str].connect(callback)
    return line_edit


def create_spin_box(
    parent: QWidget, value: int, callback: Callable
) -> QSpinBox:
    spin_box = QSpinBox(parent)
    spin_box.setValue(value)
    spin_box.valueChanged[int].connect(callback)
    return spin_box


def create_file_chooser_button(
    ui_app: QApplication,
    parent: QWidget,
    value: Optional[str],
    callback: Callable[[str], None],
) -> QPushButton:
    button = create_button(
        parent,
        label=_('Choose'),
        callback=partial(
            on_file_chooser_button_clicked,
            parent=parent,
            value=value,
            callback=callback,
        ),
        icon_pixmap=create_icon_pixmap(ui_app, QStyle.SP_DirOpenIcon),
    )
    return button


def on_file_chooser_button_clicked(
    parent: QWidget, value: str, callback: Callable
):
    value = QFileDialog.getExistingDirectory(parent, 'Choose directory', value)
    callback(value)


def image_to_pixmap(image: Image.Image) -> QPixmap:
    with io.BytesIO() as f:
        image.save(f, format='PNG')
        f.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(f.read())
    return pixmap


def create_icon_pixmap(
    app: QApplication, standard_pixmap: QStyle.StandardPixmap
) -> QPixmap:
    style = app.style()
    pixmap = style.standardPixmap(standard_pixmap)
    return pixmap


def get_icon_size(app: QApplication, pixel_metric: QStyle.PixelMetric) -> int:
    style = app.style()
    size = style.pixelMetric(pixel_metric)
    return size


def create_icon(pixmap: QPixmap) -> QIcon:
    return QIcon(pixmap)


class RootPathForm(QVBoxLayout):
    _ui_app: QApplication
    _root_path: str
    _parent: QWidget

    def __init__(
        self,
        ui_app: QApplication,
        root_path: str,
        on_change: Callable[[str], None],
        parent: QWidget,
    ):
        self._ui_app = ui_app
        self._root_path = root_path
        self._on_change = on_change
        self._parent = parent
        super().__init__()
        self._init_button()

    def _init_button(self):
        button = create_file_chooser_button(
            self._ui_app,
            self._parent,
            value=self._root_path or '',
            callback=self._on_dir_changed,
        )
        self.addWidget(button)

    def _on_dir_changed(self, path: str):
        self._on_change(path)

    def toggle(self, enabled: bool):
        for i in range(self.count()):
            item = self.itemAt(i)
            widget = item.widget()
            widget.setEnabled(enabled)


class NamedDir(NamedTuple):
    path: str = ''
    name: str = ''


class NamedDirsForm(QGridLayout):
    _ui_app: QApplication
    _named_dirs_list: List[NamedDir]
    _parent: QWidget

    def __init__(
        self,
        ui_app: QApplication,
        named_dirs: TNamedDirs,
        on_change: Callable[[TNamedDirs], None],
        parent: QWidget,
    ):
        self._ui_app = ui_app
        self._named_dirs_list = [
            NamedDir(path, name) for path, name in named_dirs.items()
        ]
        self._on_change = on_change
        self._parent = parent
        super().__init__(self._parent)
        self.setSpacing(10)
        self._init_line_edits()

    def _init_line_edits(self):
        for i, named_dir in enumerate(self._named_dirs_list):
            name_line_edit = create_line_edit(
                self._parent,
                value=named_dir.name or '',
                callback=partial(self._on_name_changed, i),
            )
            self.addWidget(name_line_edit, i, 0)
            choose_button = create_file_chooser_button(
                self._ui_app,
                self._parent,
                value=named_dir.path or None,
                callback=partial(self._on_path_changed, i),
            )
            self.addWidget(choose_button, i, 1)
            remove_button = create_button(
                self._parent,
                icon_pixmap=create_icon_pixmap(
                    self._ui_app, QStyle.SP_TrashIcon
                ),
                callback=partial(self._on_remove_clicked, i),
            )
            self.addWidget(remove_button, i, 2)
        add_button = create_button(
            self._parent,
            callback=self._on_add_clicked,
            icon_pixmap=create_icon_pixmap(
                self._ui_app, QStyle.SP_DialogOpenButton
            ),  # TODO: Icon "add"
        )
        self.addWidget(add_button, len(self._named_dirs_list), 2)

    def _clear(self):
        while self.count():
            item = self.itemAt(0)
            item.widget().deleteLater()
            self.removeItem(item)

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
        self._init_line_edits()

    def _on_add_clicked(self):
        new_named_dir = NamedDir()
        self._named_dirs_list.append(new_named_dir)
        self._on_change(self._named_dirs)
        self._clear()
        self._init_line_edits()

    @property
    def _named_dirs(self) -> TNamedDirs:
        return {
            named_dir.path: named_dir.name
            for named_dir in self._named_dirs_list
            if named_dir.path and named_dir.name
        }

    def toggle(self, enabled: bool):
        for i in range(self.count()):
            item = self.itemAt(i)
            widget = item.widget()
            widget.setEnabled(enabled)
