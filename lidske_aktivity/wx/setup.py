from functools import partial
from typing import Callable, List

import wx
import wx.adv

from lidske_aktivity.config import (
    DEFAULT_NAMED_DIRS, MODE_NAMED, Config, TNamedDirs,
)
from lidske_aktivity.wx.lib import NamedDirsForm, create_label


def add_text_heading(parent: wx.Window, sizer: wx.Sizer, text: str):
    label = create_label(parent, text)
    sizer.Add(label, flag=wx.BOTTOM, border=10)


def add_text_paragraph(parent: wx.Window, sizer: wx.Sizer, text: str):
    label = create_label(parent, text)
    sizer.Add(label, flag=wx.BOTTOM, border=5)


def add_text_list(parent: wx.Window, sizer: wx.Sizer, items: List[str]):
    for item in items:
        label = create_label(parent, f'\N{BULLET} {item}')
        sizer.Add(label)
    sizer.AddSpacer(5)


def init_wizard(wizard: wx.adv.Wizard,
                page_funcs: List[Callable],
                callback: Callable):
    pages = []
    for page_func in page_funcs:
        page = wx.adv.WizardPageSimple(wizard)
        content = page_func(parent=page)
        page.SetSizer(content)
        pages.append(page)
    wx.adv.WizardPageSimple.Chain(*pages)
    wizard.GetPageAreaSizer().Add(pages[0])
    val = wizard.RunWizard(pages[0])
    if val:
        callback()


def create_content_intro(parent: wx.Panel) -> wx.BoxSizer:
    sizer = wx.BoxSizer()
    add_text_heading(parent, sizer, 'Lidské aktivity setup')
    add_text_paragraph(
        parent,
        sizer,
        'Please adjust your OS settings like this:'
    )
    add_text_list(
        parent,
        sizer,
        [
            'first do this',
            'than that',
            'and finally something different',
        ]
    )
    return sizer


class Setup(wx.adv.Wizard):
    title = 'Lidské aktivity setup'
    _config: Config

    def __init__(self, config: Config, on_finish: Callable, parent: wx.Frame):
        self._config = config
        self._config.mode = MODE_NAMED
        if not self._config.named_dirs:
            self._config.named_dirs = DEFAULT_NAMED_DIRS
        self._on_finish = on_finish
        super().__init__(parent)
        init_wizard(
            self,
            [
                create_content_intro,
                partial(
                    NamedDirsForm,
                    self._config.named_dirs,
                    self._on_named_dirs_change
                ),
            ],
            self._on_wizard_accept
        )

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _on_wizard_accept(self):
        self._on_finish(self._config)
