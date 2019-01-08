import logging
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

from lidske_aktivity.config import Config
from lidske_aktivity.directories import Directory, TDirectories
from lidske_aktivity.utils import math

logger = logging.getLogger(__name__)

TPending = Dict[Path, bool]
TFractions = Dict[Path, float]

SIZE_MODE_SIZE = 'size'
SIZE_MODE_SIZE_NEW = 'size_new'


def calc_size(directories: TDirectories) -> Tuple[TFractions, TFractions]:
    total_size = sum(d.size or 0 for d in directories.values())
    fractions = {
        path: math.safe_div(directory.size, total_size)
        for path, directory in directories.items()
    }
    return fractions, fractions


def calc_size_new(directories: TDirectories) -> Tuple[TFractions, TFractions]:
    fractions = {
        path: math.safe_div(directory.size_new, directory.size)
        for path, directory in directories.items()
    }
    total_fractions = sum(fractions.values())
    percents = {
        path: math.safe_div(fraction, total_fractions)
        for path, fraction in fractions.items()
    }
    return fractions, percents


CALC = {
    SIZE_MODE_SIZE: calc_size,
    SIZE_MODE_SIZE_NEW: calc_size_new,
}


class Store:
    _config: Config
    _directories: TDirectories
    pending: TPending
    fractions: TFractions
    percents: TFractions
    _active_mode: str = SIZE_MODE_SIZE
    on_config_change: Optional[Callable] = None

    def __init__(self, config: Config, on_config_change: Callable):
        self._config = config
        self._directories = {}
        self.pending = {}
        self.fractions = {}
        self.percents = {}
        self.on_config_change = on_config_change

    def calc_fractions(self):
        self.fractions, self.percents = CALC[self.active_mode](
            self.directories
        )

    def update(self, path: Path, directory: Directory):
        self.directories[path] = directory
        self.pending[path] = False
        self.calc_fractions()

    @property
    def active_mode(self):
        return self._active_mode

    @active_mode.setter
    def active_mode(self, mode: str):
        self._active_mode = mode
        self.calc_fractions()

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, config: Config):
        logger.info('Config changed')
        self._config = config
        if self.on_config_change:
            self.on_config_change()

    @property
    def directories(self) -> TDirectories:
        return self._directories

    @directories.setter
    def directories(self, directories: TDirectories):
        self._directories = directories
        self.pending = {path: True for path in directories.keys()}
        self.fractions = {path: 0 for path in directories.keys()}
