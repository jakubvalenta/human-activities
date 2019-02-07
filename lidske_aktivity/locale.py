import gettext
import os
import os.path
import sys

from lidske_aktivity import __application_name__
from lidske_aktivity.vendor import gettext_windows

translation_kwargs = {}
if getattr(sys, 'frozen', False):  # Running in a bundle
    bundle_dir = sys._MEIPASS  # type: ignore
    translation_kwargs['localedir'] = os.path.join(bundle_dir, 'locale')

gettext_windows.setup_env()

t = gettext.translation(
    __application_name__, **translation_kwargs, fallback=True
)
_ = t.gettext
