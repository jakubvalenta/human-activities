import json
import os.path
from dataclasses import dataclass
from pathlib import Path


def get_env_path(var: str, default_dir: str) -> Path:
    val = os.environ.get(var)
    if val is not None:
        return Path(val)
    return Path.home() / default_dir


XDG_CACHE_HOME = get_env_path('XDG_CACHE_HOME', '.cache')
XDG_CONFIG_HOME = get_env_path('XDG_CONFIG_HOME', '.config')
PACKAGE_NAME = 'lidske-aktivity'
CONFIG_PATH = XDG_CONFIG_HOME / PACKAGE_NAME / 'config.json'
CACHE_PATH = XDG_CACHE_HOME / PACKAGE_NAME / 'cache.csv'


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
