import os
import platform
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable, Union

__application_id__ = 'cz.jakubvalenta.human-activities'
__application_name__ = 'human-activities'

__title__ = 'Human Activities'
__version__ = '0.11.0'

__summary__ = 'Monitor size of directories'
__uri__ = 'https://lab.saloun.cz/jakub/human-activities'

__authors__ = ['Jakub Valenta', 'Jiří Skála']
__author_email__ = 'jakub@jakubvalenta.cz'

__license__ = 'GNU GPL 3'
__copyright__ = '\N{COPYRIGHT SIGN} 2018-2019 Jakub Valenta, Jiří Skála'


def is_win() -> bool:
    return bool(platform.win32_ver()[0])


def is_mac() -> bool:
    return bool(platform.mac_ver()[0])


def _get_xdg_dir(
    xdg_var: str, fallback_dir: str
) -> Union[Path, PurePosixPath]:
    xdg_dir = os.environ.get('XDG_CONFIG_HOME')
    if xdg_dir:
        return PurePosixPath(xdg_dir) / __application_name__
    return Path.home() / fallback_dir


def get_xdg_cache_dir() -> Union[Path, PurePosixPath]:
    return _get_xdg_dir('XDG_CACHE_HOME', '.cache')


def get_xdg_config_dir() -> Union[Path, PurePosixPath]:
    return _get_xdg_dir('XDG_CONFIG_HOME', '.config')


def get_dir(
    mac_dir: str, xdg_func: Callable[[], Union[Path, PurePosixPath]]
) -> Union[Path, PurePosixPath, PureWindowsPath]:
    if is_win():
        win_app_dir = os.environ.get('APPDATA')
        if win_app_dir:
            return PureWindowsPath(win_app_dir) / __application_name__
    elif is_mac():
        return Path.home() / mac_dir / __application_id__
    return xdg_func() / __application_name__


def get_cache_dir():
    return get_dir('Caches', get_xdg_cache_dir)


def get_config_dir():
    return get_dir('Preferences', get_xdg_config_dir)


CACHE_PATH = Path(get_cache_dir()) / 'cache.db'
CONFIG_PATH = Path(get_config_dir()) / 'config.json'
