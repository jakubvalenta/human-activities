from functools import partial
from pathlib import Path
from typing import Callable, Dict, List

import wx
import wx.adv

from lidske_aktivity.config import DEFAULT_NAMED_DIRS, MODE_NAMED, Config
from lidske_aktivity.wx.lib import (
    choose_dir, create_button, create_label, create_sizer, create_text_control,
)


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
                on_finish: Callable):
    pages = []
    for page_func in page_funcs:
        page = wx.adv.WizardPageSimple(wizard)
        page_func(page)
        pages.append(page)
    wx.adv.WizardPageSimple.Chain(*pages)
    wizard.GetPageAreaSizer().Add(pages[0])
    val = wizard.RunWizard(pages[0])
    if val:
        on_finish()


def add_content_intro(parent: wx.Panel):
    sizer = create_sizer(parent)
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


class Setup(wx.adv.Wizard):
    title = 'Lidské aktivity setup'
    config: Config
    on_finish: Callable
    text_controls: Dict[str, wx.TextCtrl]
    named_dirs_by_name: Dict[str, Path]

    def __init__(self, config: Config, on_finish: Callable, parent: wx.Frame):
        self._init_config(config)
        self._on_finish = on_finish
        super().__init__(parent)
        init_wizard(
            self,
            [
                add_content_intro,
                self._add_content_setup,
            ],
            self.on_finish
        )

    def on_finish(self):
        self._on_finish(self.config)

    def _init_config(self, config: Config):
        self.config = config
        self.config.mode = MODE_NAMED
        if not self.config.named_dirs:
            self.config.named_dirs = DEFAULT_NAMED_DIRS
        self.named_dirs_by_name = dict(zip(
            self.config.named_dirs.values(),
            self.config.named_dirs.keys(),
        ))

    def _add_content_setup(self, parent: wx.Panel):
        sizer = create_sizer(parent)
        self.text_controls = {}
        for i, (path, name) in enumerate(self.config.named_dirs.items()):
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            label = create_label(parent, name)
            hbox.Add(
                label,
                proportion=2,
                flag=wx.EXPAND | wx.RIGHT,
                border=10
            )
            text_control = create_text_control(
                parent,
                value=str(path) or '',
                callback=partial(self.on_named_dir_text, name)
            )
            hbox.Add(
                text_control,
                proportion=3,
                flag=wx.EXPAND | wx.RIGHT,
                border=10
            )
            button = create_button(
                parent,
                parent,
                'Choose',
                partial(self.on_named_dir_button, name)
            )
            hbox.Add(button, proportion=1, flag=wx.EXPAND)
            if i == 0:
                flag = wx.EXPAND
            else:
                flag = wx.EXPAND | wx.TOP
            sizer.Add(hbox, flag=flag, border=5)
            self.text_controls[name] = text_control

    def _update_named_dirs(self, name: str, path: Path):
        self.named_dirs_by_name[name] = path
        self.config.named_dirs = dict(zip(
            self.named_dirs_by_name.values(),
            self.named_dirs_by_name.keys()
        ))

    def on_named_dir_text(self, name: str, event):
        self._update_named_dirs(name, Path(event.GetString()))

    def on_named_dir_button(self, name: str, event):
        def callback(path_str: str):
            self._update_named_dirs(name, Path(path_str))
            self.text_controls[name].SetValue(path_str)

        choose_dir(self, callback)
