import logging
import textwrap
from pathlib import Path
from typing import Callable, Dict, Optional

from lidske_aktivity.config import MODE_NAMED, Config
from lidske_aktivity.directories import Directory, TDirectories
from lidske_aktivity.utils import math

logger = logging.getLogger(__name__)

TPending = Dict[Path, bool]
TFractions = Dict[Path, float]

SIZE_MODE_SIZE = 'size'
SIZE_MODE_SIZE_NEW = 'size_new'


def calc_size_fractions(directories: TDirectories) -> TFractions:
    total_size = sum(d.size or 0 for d in directories.values())
    return {
        path: math.safe_div(directory.size, total_size)
        for path, directory in directories.items()
    }


def calc_size_new_fractions(directories: TDirectories) -> TFractions:
    return {
        path: math.safe_div(directory.size_new, directory.size)
        for path, directory in directories.items()
    }


CALC_FRACTIONS = {
    SIZE_MODE_SIZE: calc_size_fractions,
    SIZE_MODE_SIZE_NEW: calc_size_new_fractions,
}


class Store:
    _config: Config
    _directories: TDirectories
    pending: TPending
    fractions: TFractions
    active_mode: str = SIZE_MODE_SIZE
    on_config_change: Optional[Callable] = None

    def __init__(self, config: Config, on_config_change: Callable):
        self._config = config
        self._directories = {}
        self.pending = {}
        self.fractions = {}
        self.on_config_change = on_config_change

    def calc_fractions(self):
        self.fractions = CALC_FRACTIONS[self.active_mode](self.directories)

    def update(self, path: Path, directory: Directory):
        self.directories[path] = directory
        self.pending[path] = False
        self.calc_fractions()

    def set_active_mode(self, mode: str):
        self.active_mode = mode
        self.calc_fractions()

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, value: Config):
        logger.info('Config changed')
        self._config = value
        if self.on_config_change:
            self.on_config_change()

    @property
    def directories(self) -> TDirectories:
        return self._directories

    @directories.setter
    def directories(self, value: TDirectories):
        self._directories = value
        self.pending = {path: True for path in value.keys()}
        self.fractions = {path: 0 for path in value.keys()}

    def get_text(self, path: Path) -> str:
        if self.config.mode == MODE_NAMED and path in self.config.named_dirs:
            return self.config.named_dirs[path]
        return path.name

    def get_tooltip(self, path: Path) -> str:
        fraction = self.fractions[path]
        if self.active_mode == SIZE_MODE_SIZE:
            s = f'{fraction:.2%} of the size of all configured directories'
        else:
            s = (f'{fraction:.2%} of the files in this directory was modified '
                 'in the past 30 days')
        return textwrap.fill(s)
