from functools import partial
from typing import Callable, List

import wx
import wx.adv

from lidske_aktivity import texts
from lidske_aktivity.config import Config, TNamedDirs
from lidske_aktivity.wx.lib import NamedDirsForm, create_label, create_sizer


def add_text_heading(parent: wx.Window, sizer: wx.Sizer, text: str):
    label = create_label(parent, text)
    sizer.Add(label, flag=wx.BOTTOM, border=10)


def add_text_paragraph(parent: wx.Window, sizer: wx.Sizer, text: str):
    label = create_label(parent, text)
    sizer.Add(label, flag=wx.BOTTOM, border=5)


def add_text_list(parent: wx.Window, sizer: wx.Sizer, items: List[str]):
    for item in items:
        label = create_label(parent, texts.LIST_BULLET.format(item=item))
        sizer.Add(label)
    sizer.AddSpacer(5)


def add_content_intro(parent: wx.Panel):
    sizer = create_sizer(parent)
    add_text_heading(parent, sizer, texts.SETUP_TITLE)
    add_text_paragraph(parent, sizer, texts.SETUP_HEADING)
    add_text_list(parent, sizer, texts.SETUP_LIST.splitlines())


def init_wizard(
    wizard: wx.adv.Wizard, page_funcs: List[Callable], callback: Callable
):
    pages = []
    for page_func in page_funcs:
        page = wx.adv.WizardPageSimple(wizard)
        page_func(page)
        pages.append(page)
    wx.adv.WizardPageSimple.Chain(*pages)
    wizard.GetPageAreaSizer().Add(pages[0])
    val = wizard.RunWizard(pages[0])
    if val:
        callback()


class Setup(wx.adv.Wizard):
    title = texts.SETUP_TITLE

    _config: Config

    def __init__(self, config: Config, on_finish: Callable, parent: wx.Frame):
        self._config = config
        self._config.reset_named_dirs()
        self._on_finish = on_finish
        super().__init__(parent, title=self.title)
        init_wizard(
            self,
            [
                add_content_intro,
                partial(
                    NamedDirsForm,
                    self._config.named_dirs,
                    self._on_named_dirs_change,
                    use_parent_panel=True,
                ),
            ],
            self._on_wizard_accept,
        )

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _on_wizard_accept(self):
        self._on_finish(self._config)
