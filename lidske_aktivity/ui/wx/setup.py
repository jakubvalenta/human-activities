from lidske_aktivity.ui.wx.dialog import BaseDialog
from lidske_aktivity.ui.wx.lib import (
    add_text_heading, add_text_list, add_text_paragraph,
)


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
        pass
