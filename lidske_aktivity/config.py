import json
import logging
import os.path
import platform
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import List, Union

logger = logging.getLogger(__name__)

PACKAGE_NAME = 'lidske-aktivity'
PACKAGE_ID = 'com.example.lidske-aktivity'


def get_dir(mac_dir: str,
            xdg_var: str,
            fallback_dir: str) -> Union[Path, PurePosixPath, PureWindowsPath]:
    if platform.win32_ver()[0]:
        win_app_dir = os.environ.get('APPDATA')
        if win_app_dir:
            return PureWindowsPath(win_app_dir) / PACKAGE_NAME
    elif platform.mac_ver()[0]:
        return Path.home() / mac_dir / PACKAGE_ID
    else:
        xdg_cache_dir = os.environ.get(xdg_var)
        if xdg_cache_dir:
            return PurePosixPath(xdg_cache_dir) / PACKAGE_NAME
    return Path.home() / fallback_dir / PACKAGE_NAME


def get_cache_dir():
    return get_dir('Caches', 'XDG_CACHE_HOME', '.cache')


def get_config_dir():
    return get_dir('Preferences', 'XDG_CONFIG_HOME', '.config')


CACHE_PATH = Path(get_cache_dir()) / 'cache.csv'
CONFIG_PATH = Path(get_config_dir()) / 'config.json'


@dataclass
class Config:
    root_path: Path
    test: bool
    mode: str
    custom_dirs: List[str]


MODE_HOME = 'home'
MODE_CUSTOM = 'custom'
MODES = [MODE_HOME, MODE_CUSTOM]


def load_config() -> Config:
    root_path = Path.home()
    test = False
    mode = MODE_HOME
    custom_dirs = ['aaa', 'bbb']
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open() as f:
            config_json = json.load(f)
        if type(config_json.get('root_path')) == str:
            root_path = Path(config_json['root_path']).expanduser()
        if type(config_json.get('test')) == bool:
            test = config_json['test']
        mode_ = config_json.get('mode')
        if type(mode_) == str and mode_ in MODES:
            mode = mode_
        custom_dirs_ = config_json.get('custom_dirs')
        if (type(custom_dirs_) == list
                and all(type(x) == 'str' for x in custom_dirs_)):
            custom_dirs = custom_dirs_
    return Config(
        root_path=root_path,
        test=test,
        mode=mode,
        custom_dirs=custom_dirs,
    )


def clean_cache():
    if CACHE_PATH.is_file():
        CACHE_PATH.unlink()
        logger.info('Removed cache file %s', CACHE_PATH)
    else:
        logger.info('Nothing to do, cache file %s doesn\'t exist', CACHE_PATH)
