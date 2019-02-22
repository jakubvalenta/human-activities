import io
import logging
import os.path
from functools import partial
from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Union,
)

from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from human_activities import texts
from human_activities.config import NamedDirs

logger = logging.getLogger(__name__)


def create_layout() -> QVBoxLayout:
    return QVBoxLayout()


def add_layout_items(
    layout: QLayout, items: Iterable[Union[QWidget, QLayout]]
):
    for item in items:
        if isinstance(item, QWidget):
            layout.addWidget(item)
        else:
            layout.addLayout(item)


def get_layout_widgets(layout: QLayout) -> Iterator[QWidget]:
    for i in range(layout.count()):
        item = layout.itemAt(i)
        sub_layout = item.layout()
        if sub_layout:
            yield from get_layout_widgets(sub_layout)
        else:
            widget = item.widget()
            if widget:
                yield widget


def toggle_layout_widgets(layout: QLayout, enabled: bool):
    for widget in get_layout_widgets(layout):
        widget.setEnabled(enabled)


def remove_layout_items(layout: QLayout):
    for widget in get_layout_widgets(layout):
        widget.deleteLater()
    while layout.count():
        item = layout.itemAt(0)
        layout.removeItem(item)


def create_group_box(label: str, parent: QWidget) -> QGroupBox:
    group_box = QGroupBox(label, parent)
    layout = create_layout()
    group_box.setLayout(layout)
    return group_box


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
    group = QButtonGroup(parent)
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
        group.addButton(radio)
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


class FileChooserForm(QHBoxLayout):
    _parent: QWidget
    _edit: QLineEdit
    _value: str

    def __init__(
        self,
        ui_app: QApplication,
        parent: QWidget,
        value: Optional[str],
        callback: Callable[[str], None],
    ):
        self._parent = parent
        self._callback = callback
        super().__init__()
        self._value = value or ''
        self._edit = create_line_edit(
            self._parent, self._value, self._on_edit_changed
        )
        self.addWidget(self._edit)
        button = create_button(
            parent,
            label=texts.BUTTON_BROWSE,
            callback=self._on_button_clicked,
            icon_pixmap=create_icon_pixmap(ui_app, QStyle.SP_DialogOpenButton),
        )
        self.addWidget(button)
        self.setSpacing(0)

    def _on_button_clicked(self):
        self._value = QFileDialog.getExistingDirectory(
            self._parent, 'Choose directory', self._value
        )
        if self._value:
            self._edit.setText(self._value)
            self._callback(self._value)

    def _on_edit_changed(self, value: str):
        self._value = value
        self._callback(self._value)


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
    pixmap = style.standardPixmap(standard_pixmap, None)
    return pixmap


def get_icon_size(app: QApplication, pixel_metric: QStyle.PixelMetric) -> int:
    style = app.style()
    size = style.pixelMetric(pixel_metric)
    return size


def create_icon(pixmap: QPixmap) -> QIcon:
    return QIcon(pixmap)


class RootPathForm(QVBoxLayout):
    _ui_app: QApplication
    _root_path: Optional[str]
    _parent: QWidget

    def __init__(
        self,
        ui_app: QApplication,
        root_path: Optional[str],
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
        file_chooser_form = FileChooserForm(
            self._ui_app,
            self._parent,
            value=self._root_path or '',
            callback=self._on_dir_changed,
        )
        self.addLayout(file_chooser_form)

    def _on_dir_changed(self, path: str):
        self._on_change(path)


class NamedDir(NamedTuple):
    path: str = ''
    name: str = ''


class NamedDirsForm(QVBoxLayout):
    _ui_app: QApplication
    _named_dirs_list: List[NamedDir]
    _max_len: int
    _parent: QWidget
    _custom_names_enabled: bool

    def __init__(
        self,
        ui_app: QApplication,
        named_dirs: NamedDirs,
        on_change: Callable[[NamedDirs], None],
        parent: QWidget,
        custom_names_enabled: bool = True,
    ):
        self._ui_app = ui_app
        self._named_dirs_list = [
            NamedDir(path, name) for path, name in named_dirs.items()
        ]
        self._max_len = named_dirs.max_len
        self._on_change = on_change
        self._parent = parent
        self._custom_names_enabled = custom_names_enabled
        super().__init__(self._parent)
        self._init_line_edits()

    def _init_line_edits(self):
        grid = QGridLayout(self._parent)
        for i, named_dir in enumerate(self._named_dirs_list):
            left = 0
            if self._custom_names_enabled:
                name_line_edit = create_line_edit(
                    self._parent,
                    value=named_dir.name or '',
                    callback=partial(self._on_name_changed, i),
                )
                grid.addWidget(name_line_edit, i, left)
                left += 1
            file_chooser_form = FileChooserForm(
                self._ui_app,
                self._parent,
                value=named_dir.path or None,
                callback=partial(self._on_path_changed, i),
            )
            grid.addLayout(file_chooser_form, i, left)
            left += 1
            remove_button = create_button(
                self._parent,
                label=texts.BUTTON_REMOVE,
                callback=partial(self._on_remove_clicked, i),
            )
            grid.addWidget(remove_button, i, left)
            left += 1
        self.addLayout(grid)
        if len(self._named_dirs_list) < self._max_len:
            add_button = create_button(
                self._parent,
                label=texts.BUTTON_ADD,
                callback=self._on_add_clicked,
            )
            self.addWidget(add_button, alignment=Qt.AlignLeft)
        else:
            label = create_label(
                self._parent,
                texts.SETTINGS_MAX_DIRS_REACHED.format(max_len=self._max_len),
            )
            self.addWidget(label)

    def _clear(self):
        remove_layout_items(self)

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
    def _named_dirs(self) -> NamedDirs:
        return NamedDirs(
            {
                named_dir.path: named_dir.name
                or os.path.basename(named_dir.path)
                for named_dir in self._named_dirs_list
                if named_dir.path
            }
        )