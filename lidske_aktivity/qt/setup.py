from functools import partial
from typing import Callable, List

from PyQt5 import QtWidgets

from lidske_aktivity import texts
from lidske_aktivity.config import Config, TNamedDirs
from lidske_aktivity.qt.lib import NamedDirsForm, create_label, create_layout


def add_text_heading(
    parent: QtWidgets.QWidget, layout: QtWidgets.QVBoxLayout, text: str
):
    label = create_label(parent, text)
    layout.addWidget(label)


def add_text_paragraph(
    parent: QtWidgets.QWidget, layout: QtWidgets.QVBoxLayout, text: str
):
    label = create_label(parent, text)
    layout.addWidget(label)


def add_text_list(
    parent: QtWidgets.QWidget, layout: QtWidgets.QVBoxLayout, items: List[str]
):
    for item in items:
        label = create_label(parent, texts.LIST_BULLET.format(item=item))
        layout.addWidget(label)


def create_content_intro(parent: QtWidgets.QWidget) -> QtWidgets.QVBoxLayout:
    layout = create_layout()
    add_text_heading(parent, layout, texts.SETUP_TITLE)
    add_text_paragraph(parent, layout, texts.SETUP_HEADING)
    add_text_list(parent, layout, texts.SETUP_LIST.splitlines())
    return layout


def init_wizard(
    wizard: QtWidgets.QWizard,
    page_funcs: List[Callable],
    callback: Callable,
    title: str,
):
    for page_func in page_funcs:
        page = QtWidgets.QWizardPage()
        layout = page_func(page)
        page.setLayout(layout)
        wizard.addPage(page)
    wizard.setWindowTitle(title)
    if wizard.exec_():
        callback()


class Setup(QtWidgets.QWizard):
    _config: Config

    def __init__(
        self,
        config: Config,
        on_finish: Callable,
        ui_app: QtWidgets.QApplication,
    ):
        self._config = config
        self._config.reset_named_dirs()
        self._on_finish = on_finish
        super().__init__(parent=None)
        init_wizard(
            self,
            [
                create_content_intro,
                partial(
                    NamedDirsForm,
                    ui_app,
                    self._config.named_dirs,
                    self._on_named_dirs_change,
                ),
            ],
            self._on_wizard_accept,
            texts.SETUP_TITLE,
        )

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _on_wizard_accept(self):
        self._on_finish(self._config)
