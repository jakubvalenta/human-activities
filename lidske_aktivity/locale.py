import gettext
import os
import os.path
import sys

from lidske_aktivity import __application_name__
from lidske_aktivity.vendor import gettext_windows

gettext_windows.setup_env()

if getattr(sys, 'frozen', False):  # Running in a bundle
    bundle_dir = sys._MEIPASS  # type: ignore
    localedir = os.path.join(bundle_dir, 'locale')
    t = gettext.translation(__application_name__, localedir, fallback=True)
else:
    t = gettext.translation(__application_name__, fallback=True)

_ = t.gettext
