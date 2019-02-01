import gettext
import os
import sys

from lidske_aktivity import __application_name__

if sys.platform.startswith('win'):
    import locale
    if os.getenv('LANG') is None:
        lang, enc = locale.getdefaultlocale()
        os.environ['LANG'] = lang
    localedir = 'locale'
else:
    localedir = None
t = gettext.translation(__application_name__, localedir)
_ = t.gettext
