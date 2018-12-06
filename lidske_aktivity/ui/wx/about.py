import wx

from lidske_aktivity import __version__
from lidske_aktivity.ui.wx.lib import create_label


class About(wx.Dialog):
    def __init__(self, parent: wx.Frame):
        super().__init__()
        self.Create(parent, id=-1, title='About Lidské aktivity')
        # TODO: Add about icon

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = create_label(self, text='Lidské aktivity')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, '\u00a9 2018 Jakub Valenta, Jiří Skála')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, 'License: GNU General Public License')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, __version__)
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        # TODO: Fill website
        label = create_label(self, 'https://www.example.com')
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        button_sizer = wx.StdDialogButtonSizer()
        button = wx.Button(self, wx.ID_OK)
        button.SetDefault()
        button_sizer.AddButton(button)
        button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(button)
        button_sizer.Realize()
        sizer.Add(button_sizer, 0, wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)
