from functools import partial
from pathlib import Path
from typing import Dict, List

import wx
import wx.adv

from lidske_aktivity.config import DEFAULT_NAMED_DIRS, MODE_NAMED, Config
from lidske_aktivity.ui.wx.lib import (
    add_text_heading, add_text_list, add_text_paragraph, choose_dir,
    create_button, create_label, create_text_control,
)


class Page(wx.adv.WizardPageSimple):
    def __init__(self, parent: wx.adv.Wizard):
        super().__init__(parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)


class Setup(wx.adv.Wizard):
    title = 'Lidské aktivity setup'
    pages: List[Page]
    text_controls: Dict[str, wx.TextCtrl]
    named_dirs_by_name: Dict[str, Path]

    def __init__(self, parent: wx.Frame, config: Config):
        self.config = config
        self.config.mode = MODE_NAMED
        if not self.config.named_dirs:
            self.config.named_dirs = DEFAULT_NAMED_DIRS
        self.named_dirs_by_name = dict(zip(
            self.config.named_dirs.values(),
            self.config.named_dirs.keys(),
        ))
        super().__init__(parent)
        self.pages = [Page(self) for _ in range(2)]
        self.init_text(self.pages[0], self.pages[0].sizer)
        self.init_controls(self.pages[1], self.pages[1].sizer)
        wx.adv.WizardPageSimple.Chain(*self.pages)
        self.GetPageAreaSizer().Add(self.pages[0])

    def run(self):
        return self.RunWizard(self.pages[0])

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
        grid = wx.FlexGridSizer(cols=3, vgap=5, hgap=10)
        for path, name in self.config.named_dirs.items():
            label = create_label(parent, name)
            grid.Add(label)
            text_control = create_text_control(
                parent,
                value=str(path) or '',
                callback=partial(self.on_named_dir_text, name)
            )
            grid.Add(text_control)
            button = create_button(
                parent,
                parent,
                'Choose',
                partial(self.on_named_dir_button, name)
            )
            grid.Add(button)
            self.text_controls[name] = text_control
        sizer.Add(grid)

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
