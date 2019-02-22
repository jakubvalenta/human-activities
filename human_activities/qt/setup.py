import pkgutil
from typing import Callable

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWizard, QWizardPage

from human_activities import texts
from human_activities.config import Config, NamedDirs
from human_activities.qt.lib import NamedDirsForm


class Setup(QWizard):
    _config: Config

    def __init__(
        self, config: Config, on_finish: Callable, ui_app: QApplication
    ):
        self._config = config
        self._config.reset_named_dirs()
        super().__init__(parent=None)
        page = QWizardPage()
        page.setTitle(texts.SETUP_HEADING)
        page.setSubTitle(texts.SETUP_TEXT)
        layout = NamedDirsForm(
            ui_app,
            self._config.named_dirs,
            on_change=self._on_named_dirs_change,
            parent=page,
            custom_names_enabled=False,
        )
        page.setLayout(layout)
        self.addPage(page)
        self.setWindowTitle(texts.SETUP_TITLE)
        self.setWizardStyle(QWizard.MacStyle)
        background = pkgutil.get_data(
            'human_activities.qt.data', 'qt_wizard_bg.png'
        )
        pixmap = QPixmap()
        pixmap.loadFromData(background)
        self.setPixmap(QWizard.BackgroundPixmap, pixmap)
        if self.exec_():
            on_finish(self._config)

    def sizeHint(self):
        return QSize(700, 400)

    def _on_named_dirs_change(self, named_dirs: NamedDirs):
        self._config.named_dirs = named_dirs

    def _on_wizard_accept(self):
        self._on_finish(self._config)
