import json
import logging
import os.path
from typing import Any, Dict, Optional

from lidske_aktivity import CONFIG_PATH
from lidske_aktivity.locale import _
from lidske_aktivity.utils import filesystem

logger = logging.getLogger(__name__)

TNamedDirs = Dict[str, str]

MODE_ROOT_PATH = 'path'
MODE_NAMED_DIRS = 'named'
MODES = {
    MODE_ROOT_PATH: _('All directories in selected directory'),
    MODE_NAMED_DIRS: _('Predefined directories'),
}
DEFAULT_NAMED_DIRS: TNamedDirs = {
    os.path.expanduser('~/' + name): name
    for name in (_('Paid work'), _('Unpaid work'), _('Others'))
}
UNIT_SIZE_BYTES = 'size_bytes'
UNIT_NUM_FILES = 'num_files'
UNITS = {
    UNIT_SIZE_BYTES: _('Size in bytes'),
    UNIT_NUM_FILES: _('Number of files'),
}


class Config:
    mode: str = MODE_NAMED_DIRS
    root_path: Optional[str] = None
    named_dirs: TNamedDirs
    unit: str = UNIT_SIZE_BYTES
    threshold_days_ago: int = 30
    show_setup: bool = True
    test: bool = False

    def __init__(self):
        self.named_dirs = {}

    def to_json(self) -> str:
        d = {
            'mode': self.mode,
            'root_path': self.root_path,
            'named_dirs': {
                path: name
                for path, name in self.named_dirs.items()
                if path and name
            },
            'unit': self.unit,
            'threshold_days_ago': self.threshold_days_ago,
            'show_setup': self.show_setup,
            'test': self.test,
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


def _load_config_unit(config_json: Any, config: Config):
    if config_json['unit'] in UNITS:
        config.unit = config_json['unit']


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
                _load_config_unit,
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
