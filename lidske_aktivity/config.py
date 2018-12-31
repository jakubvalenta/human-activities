import json
import logging
import os.path
import platform
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Dict, List, Optional, Union

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


MODE_HOME = 'home'
MODE_PATH = 'path'
MODE_CUSTOM = 'custom'
MODE_NAMED = 'named'
MODES = {
    MODE_HOME: 'All directories in the home directory',
    MODE_PATH: 'All directories in selected directory',
    MODE_CUSTOM: 'Custom directories',
    MODE_NAMED: 'Predefined directories',
}
DEFAULT_NAMED_DIRS: Dict[Path, str] = {
    Path('~/Paid work').expanduser(): 'Honorovaná práce',
    Path('~/Unpaid work').expanduser(): 'Nehonorovaná práce',
    Path('~/Free time').expanduser(): 'Volný čas',
    Path('~/Fun').expanduser(): 'Zábava',
    Path('~/Downloads').expanduser(): 'Stažené soubory',
}


class Config:
    root_path: Optional[Path] = None
    test: bool = False
    mode: str = MODE_NAMED
    custom_dirs: List[Path]
    named_dirs: Dict[Path, str]
    show_setup: bool = True

    def __init__(self):
        self.custom_dirs = []
        self.named_dirs = {}

    def to_json(self) -> str:
        d = {
            'root_path': str(self.root_path) if self.root_path else None,
            'test': self.test,
            'mode': self.mode,
            'custom_dirs': [str(path) for path in self.custom_dirs],
            'named_dirs': {
                str(path): name for path, name in self.named_dirs.items()
            },
            'show_setup': self.show_setup,
        }
        return json.dumps(d, indent=2)


def _load_config_root_path(config_json: Any, config: Config):
    config.root_path = Path(config_json['root_path']).expanduser()


def _load_config_test(config_json: Any, config: Config):
    config.test = bool(config_json['test'])


def _load_config_mode(config_json: Any, config: Config):
    if config_json['mode'] in MODES.keys():
        config.mode = config_json['mode']


def _load_config_custom_dirs(config_json: Any, config: Config):
    config.custom_dirs = [
        Path(path_str)
        for path_str in config_json['custom_dirs']
    ]


def _load_config_named_dirs(config_json: Any, config: Config):
    config.named_dirs = {
        Path(path_str): str(name)
        for path_str, name in config_json['named_dirs'].items()
    }


def _load_config_show_setup(config_json: Any, config: Config):
    config.show_setup = bool(config_json['show_setup'])


def load_config() -> Config:
    config = Config()
    if CONFIG_PATH.is_file():
        with CONFIG_PATH.open() as f:
            config_json = json.load(f)
            for fn in [
                _load_config_root_path,
                _load_config_test,
                _load_config_mode,
                _load_config_custom_dirs,
                _load_config_named_dirs,
                _load_config_show_setup,
            ]:
                try:
                    fn(config_json, config)
                except (KeyError, AttributeError, TypeError):
                    logger.error('Error while loading config %s', fn.__name__)
    return config


def save_config(config: Config):
    config_json = config.to_json()
    logger.info('Writing config %s', config_json)
    CONFIG_PATH.write_text(config_json)


def clean_cache():
    if CACHE_PATH.is_file():
        CACHE_PATH.unlink()
        logger.info('Removed cache file %s', CACHE_PATH)
    else:
        logger.info('Nothing to do, cache file %s doesn\'t exist', CACHE_PATH)
