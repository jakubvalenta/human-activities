import json
import logging
import os.path
import platform
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, Optional, Union

from lidske_aktivity import __application_id__, __application_name__
from lidske_aktivity.utils import filesystem

logger = logging.getLogger(__name__)

TNamedDirs = Dict[str, str]


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

MODE_ROOT_PATH = 'path'
MODE_NAMED_DIRS = 'named'
MODES = {
    MODE_ROOT_PATH: 'All directories in selected directory',
    MODE_NAMED_DIRS: 'Predefined directories',
}
DEFAULT_NAMED_DIRS: TNamedDirs = {
    os.path.expanduser('~/Paid work'): 'Honorovaná práce',
    os.path.expanduser('~/Unpaid work'): 'Nehonorovaná práce',
    os.path.expanduser('~/Free time'): 'Volný čas',
    os.path.expanduser('~/Fun'): 'Zábava',
    os.path.expanduser('~/Downloads'): 'Stažené soubory',
}
VALUE_NAME_SIZE_BYTES = 'size_bytes'
VALUE_NAME_NUM_FILES = 'num_files'
VALUE_NAMES = {
    VALUE_NAME_SIZE_BYTES: 'Size in bytes',
    VALUE_NAME_NUM_FILES: 'Number of files',
}


class Config:
    root_path: Optional[str] = None
    test: bool = False
    mode: str = MODE_NAMED_DIRS
    named_dirs: TNamedDirs
    show_setup: bool = True
    value_name: str = VALUE_NAME_SIZE_BYTES
    threshold_days_ago: int = 30

    def __init__(self):
        self.named_dirs = {}

    def to_json(self) -> str:
        d = {
            'root_path': self.root_path,
            'test': self.test,
            'mode': self.mode,
            'named_dirs': {
                path: name
                for path, name in self.named_dirs.items()
                if path and name
            },
            'show_setup': self.show_setup,
            'value_name': self.value_name,
            'threshold_days_ago': self.threshold_days_ago,
        }
        return json.dumps(d, indent=2)

    def list_effective_named_dirs(self) -> TNamedDirs:
        if self.mode == MODE_NAMED_DIRS:
            return self.named_dirs
        if self.mode == MODE_ROOT_PATH:
            if not self.root_path or not os.path.isdir(self.root_path):
                logger.error('Path %s is not a directory', self.root_path)
                return {}
            return {
                path: os.path.basename(path)
                for path in filesystem.list_dirs(self.root_path)
            }
        else:
            raise Exception(f'Invalid mode {self.mode}')

    def reset_named_dirs(self):
        self.mode = MODE_NAMED_DIRS
        if not self.named_dirs:
            self.named_dirs = DEFAULT_NAMED_DIRS


def _load_config_root_path(config_json: Any, config: Config):
    if config_json['root_path']:
        config.root_path = os.path.expanduser(str(config_json['root_path']))


def _load_config_test(config_json: Any, config: Config):
    config.test = bool(config_json['test'])


def _load_config_mode(config_json: Any, config: Config):
    if config_json['mode'] in MODES.keys():
        config.mode = config_json['mode']


def _load_config_named_dirs(config_json: Any, config: Config):
    config.named_dirs = {
        str(path): str(name)
        for path, name in config_json['named_dirs'].items()
        if path and name
    }


def _load_config_show_setup(config_json: Any, config: Config):
    config.show_setup = bool(config_json['show_setup'])


def _load_config_value_name(config_json: Any, config: Config):
    if config_json['value_name'] in VALUE_NAMES:
        config.value_name = config_json['value_name']


def _load_config_threshold_days_ago(config_json: Any, config: Config):
    config.threshold_days_ago = int(config_json['threshold_days_ago'])


def load_config() -> Config:
    config = Config()
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open() as f:
            config_json = json.load(f)
            for fn in [
                _load_config_root_path,
                _load_config_test,
                _load_config_mode,
                _load_config_named_dirs,
                _load_config_show_setup,
                _load_config_value_name,
                _load_config_threshold_days_ago,
            ]:
                try:
                    fn(config_json, config)
                except (KeyError, AttributeError, TypeError):
                    logger.error('Error while loading config %s', fn.__name__)
    return config


def save_config(config: Config):
    config_json = config.to_json()
    logger.info('Writing config %s', config_json)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(config_json)


def clean_cache():
    if CACHE_PATH.is_file():
        CACHE_PATH.unlink()
        logger.info('Removed cache file %s', CACHE_PATH)
    else:
        logger.info('Nothing to do, cache file %s doesn\'t exist', CACHE_PATH)
