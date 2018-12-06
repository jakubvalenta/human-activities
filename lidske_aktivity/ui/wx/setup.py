from pathlib import Path

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
        for s in PREDEFINED_DIRS:
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            label = create_label(self, s)
            hbox.Add(label, flag=wx.RIGHT, border=10)
            text_control = create_text_control(
                self.panel,
                value='',  # TODO
                callback=self.on_prefedined_dir_text
            )
            hbox.Add(text_control, flag=wx.EXPAND | wx.RIGHT, border=10)
            button = create_button(
                self,
                self.panel,
                'Choose',
                self.on_prefedined_dir_button
            )
            hbox.Add(button, proportion=0.6, flag=wx.EXPAND)
            self.sizer.Add(hbox, flag=wx.EXPAND)

    def on_prefedined_dir_text(self, event):
        self.config.root_path = Path(event.GetString())

    def on_prefedined_dir_button(self, event):
        def callback(path_str: str):
            self.config.root_path = Path(path_str)
            self.root_path_control.SetValue(path_str)

        choose_dir(self, callback)
