from pathlib import Path
from typing import Dict

import wx

from lidske_aktivity.config import (
    MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, MODES,
)
from lidske_aktivity.ui.wx.dialog import BaseDialog
from lidske_aktivity.ui.wx.lib import (
    choose_dir, create_button, create_label, create_text_control,
)


class Settings(BaseDialog):
    title = 'Lidské aktivity advanced settings'

    mode_radios: Dict[str, wx.RadioButton]
    root_path_panel: wx.Sizer
    root_path_control: wx.TextCtrl
    list_box: wx.ListBox
    button_panel: wx.Panel

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.create_mode_radios()
        self.add_mode_radio(MODE_HOME)
        self.add_mode_radio(MODE_PATH)
        self.init_root_path_control()
        self.add_mode_radio(MODE_CUSTOM)
        self.init_custom_dirs()
        self.add_mode_radio(MODE_NAMED)
        self.init_dialog_buttons()
        self.toggle_controls()
        self.fit()

    def create_mode_radios(self):
        label = create_label(self, 'Scan mode')
        self.sizer.Add(label, flag=wx.ALL, border=5)
        self.mode_radios = {}
        for i, (mode, label) in enumerate(MODES.items()):
            if i == 0:
                kwargs = {'style': wx.RB_GROUP}
            else:
                kwargs = {}
            radio = wx.RadioButton(self.panel, label=label, **kwargs)
            radio.Bind(wx.EVT_RADIOBUTTON, self.on_radio_toggle)
            if mode == self.config.mode:
                radio.SetValue(True)
            self.mode_radios[mode] = radio

    def add_mode_radio(self, mode: str):
        self.sizer.Add(self.mode_radios[mode], flag=wx.ALL, border=5)

    def init_root_path_control(self):
        self.root_path_panel = wx.Panel(self.panel)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.root_path_control = create_text_control(
            self.root_path_panel,
            value=str(self.config.root_path),
            callback=self.on_root_path_text
        )
        hbox.Add(self.root_path_control, flag=wx.EXPAND | wx.RIGHT, border=10)
        button = create_button(
            self,
            self.root_path_panel,
            'Choose',
            self.on_root_path_button
        )
        hbox.Add(button, proportion=0.6, flag=wx.EXPAND)
        self.root_path_panel.SetSizer(hbox)
        self.sizer.Add(self.root_path_panel, flag=wx.EXPAND)

    def init_custom_dirs(self):
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.init_custom_dirs_listbox()
        hbox.Add(self.listbox, wx.ID_ANY, flag=wx.EXPAND | wx.RIGHT, border=10)
        self.init_custom_dirs_buttons()
        hbox.Add(self.button_panel, proportion=0.6, flag=wx.EXPAND)
        self.sizer.Add(hbox, flag=wx.EXPAND)

    def toggle_controls(self):
        if self.config.mode == MODE_PATH:
            self.root_path_panel.Enable()
        else:
            self.root_path_panel.Disable()
        if self.config.mode == MODE_CUSTOM:
            self.listbox.Enable()
            self.button_panel.Enable()
        else:
            self.listbox.Disable()
            self.button_panel.Disable()

    def init_custom_dirs_listbox(self):
        self.listbox = wx.ListBox(self.panel)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.on_custom_dir_change)
        for custom_dir in self.config.custom_dirs:
            self.listbox.Append(str(custom_dir))

    def init_custom_dirs_buttons(self):
        self.button_panel = wx.Panel(self.panel)
        vbox = wx.BoxSizer(wx.VERTICAL)
        for i, (label, callback) in enumerate([
                ('New', self.on_custom_dir_new),
                ('Change', self.on_custom_dir_change),
                ('Delete', self.on_custom_dir_delete),
                ('Clear', self.on_custom_dirs_clear),
        ]):
            button = create_button(self, self.button_panel, label, callback)
            if i == 0:
                vbox.Add(button)
            else:
                vbox.Add(button, 0, flag=wx.TOP, border=5)
        self.button_panel.SetSizer(vbox)

    def on_radio_toggle(self, event):
        for mode, radio in self.mode_radios.items():
            if radio.GetValue():
                self.config.mode = mode
        self.toggle_controls()

    def on_root_path_text(self, event):
        self.config.root_path = Path(event.GetString())

    def on_root_path_button(self, event):
        def callback(path_str: str):
            self.config.root_path = Path(path_str)
            self.root_path_control.SetValue(path_str)

        choose_dir(self, callback)

    def on_custom_dir_change(self, event):
        def callback(path_str: str):
            sel = self.listbox.GetSelection()
            self.listbox.Delete(sel)
            item_id = self.listbox.Insert(path_str, sel)
            self.config.custom_dirs[sel] = Path(path_str)
            self.listbox.SetSelection(item_id)

        choose_dir(self, callback)

    def on_custom_dir_new(self, event):
        def callback(path_str: str):
            self.config.custom_dirs.append(Path(path_str))
            self.listbox.Append(path_str)

        choose_dir(self, callback)

    def on_custom_dir_delete(self, event):
        sel = self.listbox.GetSelection()
        if sel != -1:
            del self.config.custom_dirs[sel]
            self.listbox.Delete(sel)

    def on_custom_dirs_clear(self, event):
        self.config.custom_dirs[:] = []
        self.listbox.Clear()
