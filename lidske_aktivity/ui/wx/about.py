import wx

from lidske_aktivity import __version__
from lidske_aktivity.ui.wx.dialog import BaseDialog
from lidske_aktivity.ui.wx.lib import create_label


class About(BaseDialog):
    title = 'About Lidské aktivity'

    def init_content(self):
        # TODO: Add about icon
        label = create_label(self, text='Lidské aktivity')
        self.sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, '\u00a9 2018 Jakub Valenta, Jiří Skála')
        self.sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, 'License: GNU General Public License')
        self.sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        label = create_label(self, __version__)
        self.sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        # TODO: Fill website
        label = create_label(self, 'https://www.example.com')
        self.sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
