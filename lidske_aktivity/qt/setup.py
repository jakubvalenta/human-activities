from functools import partial
from typing import Callable, List

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import (
    QApplication,
    QLayout,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from lidske_aktivity import texts
from lidske_aktivity.config import Config, NamedDirs
from lidske_aktivity.qt.lib import NamedDirsForm, create_label, create_layout


def add_text_heading(parent: QWidget, layout: QVBoxLayout, text: str):
    label = create_label(parent, text)
    layout.addWidget(label)


def add_text_paragraph(parent: QWidget, layout: QVBoxLayout, text: str):
    label = create_label(parent, text)
    layout.addWidget(label)


def add_text_list(parent: QWidget, layout: QVBoxLayout, items: List[str]):
    for item in items:
        label = create_label(parent, texts.LIST_BULLET.format(item=item))
        layout.addWidget(label)


def create_content_intro(parent: QWidget) -> QVBoxLayout:
    layout = create_layout()
    add_text_heading(parent, layout, texts.SETUP_TITLE)
    add_text_paragraph(parent, layout, texts.SETUP_HEADING)
    add_text_list(parent, layout, texts.SETUP_LIST.splitlines())
    return layout


class Setup(QWizard):
    _config: Config

    def __init__(
        self, config: Config, on_finish: Callable, ui_app: QApplication
    ):
        self._config = config
        self._config.reset_named_dirs()
        super().__init__(parent=None)
        self._add_page(create_content_intro, texts.SETUP_STEP_INTRO_TITLE)
        self._add_page(
            partial(
                NamedDirsForm,
                ui_app,
                self._config.named_dirs,
                self._on_named_dirs_change,
            ),
            texts.SETUP_STEP_SETUP_TITLE
        )
        self.setWindowTitle(texts.SETUP_TITLE)
        if self.exec_():
            on_finish(self._config)

    def sizeHint(self):
        return QSize(700, 400)

    def _add_page(self, page_func: Callable[[QWizardPage], QLayout], title: str):
        page = QWizardPage()
        page.setTitle(title)
        layout = page_func(page)
        page.setLayout(layout)
        self.addPage(page)

    def _on_named_dirs_change(self, named_dirs: NamedDirs):
        self._config.named_dirs = named_dirs

    def _on_wizard_accept(self):
        self._on_finish(self._config)
