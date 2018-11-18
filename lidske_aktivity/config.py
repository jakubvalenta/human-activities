import json
import os.path
import platform
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

PACKAGE_NAME = 'lidske-aktivity'
PACKAGE_ID = 'com.example.lidske-aktivity'


def get_dir(mac_dir: str, xdg_var: str, fallback_dir: str) -> Path:
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


CACHE_PATH = get_cache_dir() / 'cache.csv'
CONFIG_PATH = get_config_dir() / 'config.json'


@dataclass
class Config:
    root_path: Path = Path.home()
    test: bool = False


def load_config() -> Config:
    if not CONFIG_PATH.is_file():
        return Config()
    kwargs = {}
    with CONFIG_PATH.open() as f:
        config_json = json.load(f)
    if 'root_path' in config_json and type(config_json['root_path']) == str:
        kwargs['root_path'] = Path(config_json['root_path']).expanduser()
    if 'test' in config_json and type(config_json['test']) == bool:
        kwargs['test'] = config_json['test']
    return Config(**kwargs)
