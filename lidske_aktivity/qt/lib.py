import io
import logging
from functools import partial
from typing import Callable, List, NamedTuple, Optional

from PIL import Image
from PyQt5 import QtGui, QtWidgets

from lidske_aktivity.config import TNamedDirs
from lidske_aktivity.texts import _

logger = logging.getLogger(__name__)


def create_layout() -> QtWidgets.QVBoxLayout:
    # TODO: Horizontal layout
    return QtWidgets.QVBoxLayout()


def create_label(parent: QtWidgets.QWidget, text: str) -> QtWidgets.QLabel:
    return QtWidgets.QLabel(text, parent)


def create_button(
    parent: QtWidgets.QWidget,
    callback: Callable,
    label: Optional[str] = None,
    icon_pixmap: Optional[QtGui.QPixmap] = None,
) -> QtWidgets.QPushButton:
    button = QtWidgets.QPushButton(parent)
    if label:
        button.setText(label)
    if icon_pixmap:
        icon = create_icon(icon_pixmap)
        button.setIcon(icon)
    button.clicked.connect(callback)
    return button


def create_line_edit(
    parent: QtWidgets.QWidget, value: str, callback: Callable
) -> QtWidgets.QLineEdit:
    line_edit = QtWidgets.QLineEdit(value, parent)
    line_edit.textChanged[str].connect(callback)
    return line_edit


def create_file_chooser_button(
    parent: QtWidgets.QWidget,
    value: Optional[str],
    callback: Callable[[str], None],
) -> QtWidgets.QPushButton:
    button = create_button(
        parent,
        label=_('Choose'),
        callback=partial(
            on_file_chooser_button_clicked, parent=parent, callback=callback
        ),
    )
    return button


def on_file_chooser_button_clicked(
    parent: QtWidgets.QWidget, callback: Callable
):
    value = QtWidgets.QFileDialog.getOpenFileName(parent, 'Open file', '/home')
    callback(value)


def image_to_pixmap(image: Image.Image) -> QtGui.QPixmap:
    with io.BytesIO() as f:
        image.save(f, format='PNG')
        f.seek(0)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(f.read())
    return pixmap


def create_icon_pixmap(
    app: QtWidgets.QApplication,
    standard_pixmap: QtWidgets.QStyle.StandardPixmap,
) -> QtGui.QPixmap:
    style = app.style()
    pixmap = style.standardPixmap(standard_pixmap)
    return pixmap


def get_icon_size(
    app: QtWidgets.QApplication, pixel_metric: QtWidgets.QStyle.PixelMetric
) -> int:
    style = app.style()
    size = style.pixelMetric(pixel_metric)
    return size


def create_icon(pixmap: QtGui.QPixmap) -> QtGui.QIcon:
    return QtGui.QIcon(pixmap)


class NamedDir(NamedTuple):
    path: str = ''
    name: str = ''


class NamedDirsForm(QtWidgets.QGridLayout):
    _ui_app: QtWidgets.QApplication
    _named_dirs_list: List[NamedDir]
    _parent: QtWidgets.QWidget

    def __init__(
        self,
        ui_app: QtWidgets.QApplication,
        named_dirs: TNamedDirs,
        on_change: Callable[[TNamedDirs], None],
        parent: QtWidgets.QWidget,
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
                self._parent,
                value=named_dir.path or None,
                callback=partial(self._on_path_changed, i),
            )
            self.addWidget(choose_button, i, 1)
            remove_button = create_button(
                self._parent,
                icon_pixmap=create_icon_pixmap(
                    self._ui_app, QtWidgets.QStyle.SP_TrashIcon
                ),
                callback=partial(self._on_remove_clicked, i),
            )
            self.addWidget(remove_button, i, 2)
        add_button = create_button(
            self._parent,
            callback=self._on_add_clicked,
            icon_pixmap=create_icon_pixmap(
                self._ui_app, QtWidgets.QStyle.SP_DialogOpenButton
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
