import gettext
import os
import os.path
import sys

import gettext_windows

from lidske_aktivity import __application_name__

if getattr(sys, 'frozen', False):  # Running in a bundle
    bundle_dir = sys._MEIPASS  # type: ignore
    locale_dir = os.path.join(bundle_dir, 'locale')
else:
    locale_dir = ''

gettext_windows.setup_env()

t = gettext.translation(__application_name__, locale_dir, fallback=True)
_ = t.gettext
