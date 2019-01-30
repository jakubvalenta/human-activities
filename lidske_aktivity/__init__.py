import gettext
import os
import platform
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Union

__application_id__ = 'cz.jakubvalenta.lidske-aktivity'
__application_name__ = 'lidske-aktivity'

__title__ = 'Lidské aktivity'
__version__ = '0.3.0'

__summary__ = 'Lidské aktivity'
__uri__ = 'https://lab.saloun.cz/jakub/art-lidske-aktivity-gtk'

__authors__ = ['Jakub Valenta', 'Jiří Skála']
__author_email__ = 'jakub@jakubvalenta.cz'

__license__ = 'GNU GPL 3'
__copyright__ = '\N{COPYRIGHT SIGN} 2018-2019 Jakub Valenta, Jiří Skála'


def get_dir(mac_dir: str,
            xdg_var: str,
            fallback_dir: str) -> Union[Path, PurePosixPath, PureWindowsPath]:
    if platform.win32_ver()[0]:
        win_app_dir = os.environ.get('APPDATA')
        if win_app_dir:
            return PureWindowsPath(win_app_dir) / __application_name__
    elif platform.mac_ver()[0]:
        return Path.home() / mac_dir / __application_id__
    else:
        xdg_cache_dir = os.environ.get(xdg_var)
        if xdg_cache_dir:
            return PurePosixPath(xdg_cache_dir) / __application_name__
    return Path.home() / fallback_dir / __application_name__


def get_cache_dir():
    return get_dir('Caches', 'XDG_CACHE_HOME', '.cache')


def get_config_dir():
    return get_dir('Preferences', 'XDG_CONFIG_HOME', '.config')


CACHE_PATH = Path(get_cache_dir()) / 'cache.db'
CONFIG_PATH = Path(get_config_dir()) / 'config.json'

LOCALE_PATH = Path(__file__).parents[1] / 'locale'
t = gettext.translation(__application_name__, LOCALE_PATH)
_ = t.gettext
