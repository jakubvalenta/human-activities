import wx

from lidske_aktivity.config import Config
from lidske_aktivity.ui.wx.lib import create_sizer


class BaseDialog(wx.Dialog):
    title: str

    panel: wx.Panel
    sizer: wx.Sizer
    border_sizer: wx.Sizer

    def __init__(self, parent: wx.Frame):
        super().__init__()
        self.Create(parent, id=-1, title=self.title)
        self.init_window()
        self.init_content()
        self.init_dialog_buttons()
        self.fit()

    def init_window(self):
        self.panel = wx.Panel(self)
        self.border_sizer = create_sizer(self.panel)
        self.sizer = create_sizer(
            self.border_sizer,
            flag=wx.EXPAND | wx.ALL,
            border=10
        )

    def init_content(self):
        raise NotImplementedError

    def init_dialog_buttons(self):
        button_sizer = wx.StdDialogButtonSizer()
        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()
        self.sizer.Add(button_sizer, flag=wx.TOP, border=10)

    def show(self):
        self.Centre()
        self.ShowModal()

    def fit(self):
        self.border_sizer.Fit(self.panel)
        self.border_sizer.Fit(self)
        self.Layout()


class BaseConfigDialog(BaseDialog):
    config: Config

    def __init__(self, parent: wx.Frame, config: Config):
        self.config = config
        super().__init__(parent)
