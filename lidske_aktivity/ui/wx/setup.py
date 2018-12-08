from functools import partial
from pathlib import Path
from typing import Dict

import wx

from lidske_aktivity.ui.wx.dialog import BaseConfigDialog
from lidske_aktivity.ui.wx.lib import (
    add_text_heading, add_text_list, add_text_paragraph, choose_dir,
    create_button, create_label, create_text_control,
)


class Setup(BaseConfigDialog):
    title = 'Lidské aktivity setup'
    text_controls: Dict[str, wx.TextCtrl]

    def init_content(self):
        self.init_text()
        self.init_controls()

    def init_text(self):
        add_text_heading(self, self.sizer, 'Lidské aktivity setup')
        add_text_paragraph(
            self,
            self.sizer,
            'Please adjust your OS settings like this:'
        )
        add_text_list(
            self,
            self.sizer,
            [
                'first do this',
                'than that',
                'and finally something different',
            ]
        )

    def init_controls(self):
        self.text_controls = {}
        sizer = wx.FlexGridSizer(cols=3, vgap=5, hgap=10)
        for name, path_str in self.config.named_dirs.items():
            label = create_label(self.panel, name)
            sizer.Add(label)
            text_control = create_text_control(
                self.panel,
                value=path_str or '',
                callback=partial(self.on_named_dir_text, name)
            )
            sizer.Add(text_control)
            button = create_button(
                self,
                self.panel,
                'Choose',
                partial(self.on_named_dir_button, name)
            )
            sizer.Add(button)
            self.text_controls[name] = text_control
        self.sizer.Add(sizer)

    def on_named_dir_text(self, name: str, event):
        self.config.named_dirs[name] = Path(event.GetString())

    def on_named_dir_button(self, name: str, event):
        def callback(path_str: str):
            self.config.named_dirs[name] = Path(path_str)
            self.text_controls[name].SetValue(path_str)

        choose_dir(self, callback)
