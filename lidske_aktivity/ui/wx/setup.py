from functools import partial
from pathlib import Path
from typing import List

import wx

from lidske_aktivity.ui.wx.dialog import BaseDialog
from lidske_aktivity.ui.wx.lib import (
    add_text_heading, add_text_list, add_text_paragraph, choose_dir,
    create_button, create_label, create_text_control,
)

PREDEFINED_DIRS = [
    'Honorovaná práce',
    'Nehonorovaná práce',
    'Volný čas',
    'Zábava',
    'Stažené soubory',
]


class Setup(BaseDialog):
    title = 'Lidské aktivity setup'
    text_controls: List[wx.TextCtrl]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_text()
        self.init_controls()
        self.init_dialog_buttons()
        self.fit()

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
        self.text_controls = []
        sizer = wx.FlexGridSizer(cols=3, vgap=5, hgap=10)
        for i, s in enumerate(PREDEFINED_DIRS):
            label = create_label(self.panel, s)
            sizer.Add(label)
            text_control = create_text_control(
                self.panel,
                value='',  # TODO
                callback=partial(self.on_prefedined_dir_text, i)
            )
            sizer.Add(text_control)
            button = create_button(
                self,
                self.panel,
                'Choose',
                partial(self.on_prefedined_dir_button, i)
            )
            sizer.Add(button)
            self.text_controls.append(text_control)
        self.sizer.Add(sizer)

    def on_prefedined_dir_text(self, i: int, event):
        self.config.custom_dirs[i] = Path(event.GetString())

    def on_prefedined_dir_button(self, i: int, event):
        def callback(path_str: str):
            self.config.custom_dirs[i] = Path(path_str)
            self.text_controls[i].SetValue(path_str)

        choose_dir(self, callback)
