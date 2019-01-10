from pathlib import Path
from typing import Callable, Dict, List

import wx

from lidske_aktivity.config import (
    MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, MODES, Config,
)
from lidske_aktivity.wx.lib import (
    CustomDirsForm, NamedDirsForm, RadioConfig, RootPathForm, TNamedDirs,
    create_label, create_radio_group, create_sizer,
)


class Settings(wx.Dialog):
    title = 'Lidské aktivity advanced settings'

    config: Config
    _panel: wx.Panel
    _sizer: wx.Sizer
    _border_sizer: wx.Sizer
    _mode_radios: Dict[str, wx.RadioButton]
    _root_path_form: RootPathForm
    _custom_dirs_form: CustomDirsForm
    _named_dirs_form: NamedDirsForm

    def __init__(self, config: Config, on_accept: Callable, parent: wx.Frame):
        self._config = config
        self._on_accept = on_accept
        super().__init__()
        self.Create(parent, id=-1, title=self.title)
        self._init_window()
        self._create_widgets()
        self._add_widgets()
        self._init_dialog_buttons()
        self._fit()
        self._show()

    def _init_window(self):
        self._border_sizer = create_sizer(self)
        self._panel = wx.Panel(self)
        self._border_sizer.Add(
            self._panel,
            proportion=1,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )
        self._sizer = create_sizer(self._panel)

    def _init_dialog_buttons(self):
        button_sizer = wx.StdDialogButtonSizer()
        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()
        self._border_sizer.Add(
            button_sizer,
            flag=wx.EXPAND | wx.TOP | wx.BOTTOM,
            border=10
        )

    def _create_widgets(self):
        self._root_path_form = RootPathForm(
            self._config.root_path,
            self._on_root_path_change,
            parent=self._panel
        )
        self._custom_dirs_form = CustomDirsForm(
            self._config.custom_dirs,
            self._on_custom_dirs_change,
            parent=self._panel
        )
        self._named_dirs_form = NamedDirsForm(
            self._config.named_dirs,
            self._on_named_dirs_change,
            parent=self._panel
        )
        self._create_mode_radios()

    def _add_widgets(self):
        label = create_label(self._panel, 'Scan mode')
        self._sizer.Add(label, flag=wx.ALL, border=5)
        self._sizer.Add(self._mode_radios[MODE_HOME], flag=wx.ALL, border=5)
        self._sizer.Add(self._mode_radios[MODE_PATH], flag=wx.ALL, border=5)
        self._sizer.Add(self._root_path_form, flag=wx.EXPAND)
        self._sizer.Add(self._mode_radios[MODE_CUSTOM], flag=wx.ALL, border=5)
        self._sizer.Add(self._custom_dirs_form, flag=wx.EXPAND)
        self._sizer.Add(self._mode_radios[MODE_NAMED], flag=wx.ALL, border=5)
        self._sizer.Add(self._named_dirs_form, flag=wx.EXPAND)
        self._toggle_controls()

    def _create_mode_radios(self):
        radio_configs = [
            RadioConfig(value, label)
            for value, label in MODES.items()
        ]
        self._mode_radios = create_radio_group(
            self._panel,
            radio_configs,
            active_value=self._config.mode,
            callback=self._on_mode_radio_toggled
        )

    def _toggle_controls(self):
        if self._config.mode == MODE_PATH:
            self._root_path_form.Enable()
        else:
            self._root_path_form.Disable()
        if self._config.mode == MODE_CUSTOM:
            self._custom_dirs_form.Enable()
        else:
            self._custom_dirs_form.Disable()
        if self._config.mode == MODE_NAMED:
            self._named_dirs_form.Enable()
        else:
            self._named_dirs_form.Disable()

    def _on_mode_radio_toggled(self, mode: str):
        self._config.mode = mode
        self._toggle_controls()

    def _on_root_path_change(self, root_path: Path):
        self._config.root_path = root_path

    def _on_custom_dirs_change(self, custom_dirs: List[Path]):
        self._config.custom_dirs = custom_dirs

    def _on_named_dirs_change(self, named_dirs: TNamedDirs):
        self._config.named_dirs = named_dirs

    def _fit(self):
        self._border_sizer.Fit(self._panel)
        self._border_sizer.Fit(self)
        self.Layout()

    def _show(self):
        self.Centre()
        val = self.ShowModal()
        if val == wx.ID_OK:
            self._on_accept(self._config)
        self.Destroy()
