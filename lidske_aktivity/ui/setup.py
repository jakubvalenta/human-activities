from functools import partial
from pathlib import Path
from typing import Callable, Dict, List

import wx
import wx.adv

from lidske_aktivity.config import DEFAULT_NAMED_DIRS, MODE_NAMED, Config
from lidske_aktivity.ui.lib import (
    add_text_heading, add_text_list, add_text_paragraph, choose_dir,
    create_button, create_label, create_sizer, create_text_control,
)


class Page(wx.adv.WizardPageSimple):
    def __init__(self, parent: wx.adv.Wizard):
        super().__init__(parent)
        self.sizer = create_sizer(self)


class Setup(wx.adv.Wizard):
    title = 'Lidské aktivity setup'
    pages: List[Page]
    text_controls: Dict[str, wx.TextCtrl]
    named_dirs_by_name: Dict[str, Path]

    def __init__(self, config: Config, on_finish: Callable, parent: wx.Frame):
        self.config = config
        self.config.mode = MODE_NAMED
        if not self.config.named_dirs:
            self.config.named_dirs = DEFAULT_NAMED_DIRS
        self.named_dirs_by_name = dict(zip(
            self.config.named_dirs.values(),
            self.config.named_dirs.keys(),
        ))
        self.on_finish = on_finish
        super().__init__(parent)
        self.pages = [Page(self) for _ in range(2)]
        self.init_text(self.pages[0], self.pages[0].sizer)
        self.init_controls(self.pages[1], self.pages[1].sizer)
        wx.adv.WizardPageSimple.Chain(*self.pages)
        self.GetPageAreaSizer().Add(self.pages[0])
        self.run()

    def run(self):
        val = self.RunWizard(self.pages[0])
        if val:
            self.on_finish(self)

    def init_text(self, parent: wx.Panel, sizer: wx.BoxSizer):
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

    def init_controls(self, parent: wx.Panel, sizer: wx.BoxSizer):
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
