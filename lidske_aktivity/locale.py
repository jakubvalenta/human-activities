import gettext
import os
import os.path
import sys

from lidske_aktivity import __application_name__

if sys.platform.startswith('win'):
    import locale
    if os.getenv('LANG') is None:
        lang, enc = locale.getdefaultlocale()
        os.environ['LANG'] = lang

if getattr(sys, 'frozen', False):  # Running in a bundle
    localedir = os.path.join(sys._MEIPASS, 'locale')
else:
    localedir = None

t = gettext.translation(__application_name__, localedir, fallback=True)
_ = t.gettext
