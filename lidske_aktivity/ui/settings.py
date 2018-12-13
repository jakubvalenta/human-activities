from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import wx

from lidske_aktivity.config import (
    MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, MODES, Config,
)
from lidske_aktivity.ui.dialog import BaseConfigDialog
from lidske_aktivity.ui.lib import (
    choose_dir, create_button, create_label, create_sizer, create_text_control,
)


class Settings(BaseConfigDialog):
    title = 'Lidské aktivity advanced settings'

    mode_radios: Dict[str, wx.RadioButton]
    root_path_panel: wx.Panel
    root_path_control: wx.TextCtrl
    custom_dirs_panel: wx.Panel
    custom_dirs_list: wx.ListBox
    named_dirs_panel: wx.Panel
    named_dirs_path_controls: List[wx.TextCtrl]
    named_dirs_list: List[Tuple[Path, str]]

    def __init__(self, parent: wx.Frame, config: Config):
        self.config = config
        self.named_dirs_list = list(zip(
            self.config.named_dirs.keys(),
            self.config.named_dirs.values(),
        ))
        super().__init__(parent, config)

    def init_content(self):
        self.create_mode_radios()
        self.add_mode_radio(MODE_HOME)
        self.add_mode_radio(MODE_PATH)
        self.init_root_path_control()
        self.add_mode_radio(MODE_CUSTOM)
        self.init_custom_dirs()
        self.add_mode_radio(MODE_NAMED)
        self.init_named_dirs()
        self.toggle_controls()

    def create_mode_radios(self):
        label = create_label(self.panel, 'Scan mode')
        self.sizer.Add(label, flag=wx.ALL, border=5)
        self.mode_radios = {}
        for i, (mode, label) in enumerate(MODES.items()):
            if i == 0:
                kwargs = {'style': wx.RB_GROUP}
            else:
                kwargs = {}
            radio = wx.RadioButton(self.panel, label=label, **kwargs)
            radio.Bind(wx.EVT_RADIOBUTTON, self.on_mode_radio)
            if mode == self.config.mode:
                radio.SetValue(True)
            self.mode_radios[mode] = radio

    def add_mode_radio(self, mode: str):
        self.sizer.Add(self.mode_radios[mode], flag=wx.ALL, border=5)

    def init_root_path_control(self):
        self.root_path_panel = wx.Panel(self.panel)
        hbox = create_sizer(self.root_path_panel, wx.HORIZONTAL)
        self.root_path_control = create_text_control(
            self.root_path_panel,
            value=str(self.config.root_path),
            callback=self.on_root_path_text
        )
        hbox.Add(
            self.root_path_control,
            proportion=5,
            flag=wx.EXPAND | wx.RIGHT,
            border=10
        )
        button = create_button(
            self,
            self.root_path_panel,
            'Choose',
            self.on_root_path_button
        )
        hbox.Add(button, proportion=1, flag=wx.EXPAND)
        self.sizer.Add(self.root_path_panel, flag=wx.EXPAND)

    def init_custom_dirs(self):
        self.custom_dirs_panel = wx.Panel(self.panel)
        hbox = create_sizer(self.custom_dirs_panel, wx.HORIZONTAL)

        self.custom_dirs_list = wx.ListBox(self.custom_dirs_panel)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.on_custom_dir_change)
        for custom_dir in self.config.custom_dirs:
            self.custom_dirs_list.Append(str(custom_dir))
        hbox.Add(
            self.custom_dirs_list,
            proportion=5,
            flag=wx.EXPAND | wx.RIGHT,
            border=10
        )

        vbox = wx.BoxSizer(wx.VERTICAL)
        for i, (label, callback) in enumerate([
                ('New', self.on_custom_dir_new),
                ('Change', self.on_custom_dir_change),
                ('Delete', self.on_custom_dir_delete),
                ('Clear', self.on_custom_dirs_clear),
        ]):
            button = create_button(
                self,
                self.custom_dirs_panel,
                label,
                callback
            )
            if i == 0:
                flag = wx.EXPAND
            else:
                flag = wx.EXPAND | wx.TOP
            vbox.Add(button, flag=flag, border=5)
        hbox.Add(vbox, proportion=1, flag=wx.EXPAND)

        self.sizer.Add(self.custom_dirs_panel, flag=wx.EXPAND)

    def init_named_dirs(self):
        self.named_dirs_panel = wx.Panel(self.panel)
        vbox = create_sizer(self.named_dirs_panel)
        self.named_dirs_path_controls = []
        for i, (path, name) in enumerate(self.named_dirs_list):
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            text_control_name = create_text_control(
                self.named_dirs_panel,
                value=name or '',
                callback=partial(self.on_named_dir_name_text, i)
            )
            hbox.Add(
                text_control_name,
                proportion=2,
                flag=wx.EXPAND | wx.RIGHT,
                border=10
            )
            text_control_path = create_text_control(
                self.named_dirs_panel,
                value=str(path) or '',
                callback=partial(self.on_named_dir_path_text, i)
            )
            hbox.Add(
                text_control_path,
                proportion=3,
                flag=wx.EXPAND | wx.RIGHT,
                border=10
            )
            button = create_button(
                self,
                self.named_dirs_panel,
                'Choose',
                partial(self.on_named_dir_button, i)
            )
            hbox.Add(button, proportion=1, flag=wx.EXPAND)
            if i == 0:
                vbox.Add(hbox, flag=wx.EXPAND)
            else:
                vbox.Add(hbox, flag=wx.EXPAND | wx.TOP, border=5)
            self.named_dirs_path_controls.append(text_control_path)
        self.sizer.Add(self.named_dirs_panel, flag=wx.EXPAND)

    def _update_named_dirs(self,
                           i: int,
                           name: Optional[str] = None,
                           path: Optional[Path] = None):
        if path is None:
            path = self.named_dirs_list[i][0]
        if name is None:
            name = self.named_dirs_list[i][1]
        self.named_dirs_list[i] = (path, name)
        self.config.named_dirs = dict(self.named_dirs_list)

    def on_named_dir_name_text(self, i: int, event):
        self._update_named_dirs(i, name=event.GetString())

    def on_named_dir_path_text(self, i: int, event):
        self._update_named_dirs(i, path=Path(event.GetString()))

    def on_named_dir_button(self, i: int, event):
        def callback(path_str: str):
            self._update_named_dirs(i, path=Path(path_str))
            self.named_dirs_path_controls[i].SetValue(path_str)

        choose_dir(self.panel, callback)

    def toggle_controls(self):
        if self.config.mode == MODE_PATH:
            self.root_path_panel.Enable()
        else:
            self.root_path_panel.Disable()
        if self.config.mode == MODE_CUSTOM:
            self.custom_dirs_panel.Enable()
        else:
            self.custom_dirs_panel.Disable()
        if self.config.mode == MODE_NAMED:
            self.named_dirs_panel.Enable()
        else:
            self.named_dirs_panel.Disable()

    def on_mode_radio(self, event):
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
            sel = self.custom_dirs_list.GetSelection()
            self.custom_dirs_list.Delete(sel)
            item_id = self.custom_dirs_list.Insert(path_str, sel)
            self.config.custom_dirs[sel] = Path(path_str)
            self.custom_dirs_list.SetSelection(item_id)

        choose_dir(self, callback)

    def on_custom_dir_new(self, event):
        def callback(path_str: str):
            self.config.custom_dirs.append(Path(path_str))
            self.custom_dirs_list.Append(path_str)

        choose_dir(self, callback)

    def on_custom_dir_delete(self, event):
        sel = self.custom_dirs_list.GetSelection()
        if sel != -1:
            del self.config.custom_dirs[sel]
            self.custom_dirs_list.Delete(sel)

    def on_custom_dirs_clear(self, event):
        self.config.custom_dirs[:] = []
        self.custom_dirs_list.Clear()
