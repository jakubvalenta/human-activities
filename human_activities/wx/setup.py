from typing import Callable

import wx
import wx.adv

from human_activities import texts
from human_activities.config import Config, NamedDirs
from human_activities.wx.lib import NamedDirsForm, create_label, create_sizer


class Setup(wx.adv.Wizard):
    _config: Config

    def __init__(self, config: Config, on_finish: Callable, parent: wx.Frame):
        self._config = config
        self._config.reset_named_dirs()
        super().__init__(parent, title=texts.SETUP_TITLE)
        page = wx.adv.WizardPageSimple(self)
        self._vbox = create_sizer(page)
        heading = create_label(
            page, markup=f'<big><b>{texts.SETUP_HEADING}</b></big>'
        )
        self._vbox.Add(heading, flag=wx.EXPAND | wx.BOTTOM, border=10)
        text = create_label(page, texts.SETUP_TEXT)
        self._vbox.Add(text, flag=wx.EXPAND | wx.BOTTOM, border=10)
        named_dirs_form = NamedDirsForm(
            self._config.named_dirs,
            self._on_named_dirs_change,
            on_redraw=self._fit,
            parent=page,
            custom_names_enabled=False,
        )
        self._vbox.Add(named_dirs_form.panel)
        self.GetPageAreaSizer().Add(page)
        val = self.RunWizard(page)
        if val:
            on_finish(self._config)

    def _on_named_dirs_change(self, named_dirs: NamedDirs):
        self._config.named_dirs = named_dirs

    def _on_wizard_accept(self):
        self._on_finish(self._config)

    def _fit(self):
        self._vbox.Layout()
        self.Fit()
