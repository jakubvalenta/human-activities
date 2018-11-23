from pathlib import Path
from typing import Dict

from lidske_aktivity.directories import Directory, TDirectories
from lidske_aktivity.utils import math

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
    directories: TDirectories
    pending: TPending
    fractions: TFractions
    active_mode: str = SIZE_MODE_SIZE

    def __init__(self, directories: TDirectories):
        self.directories = directories
        self.pending = {path: True for path in self.directories.keys()}
        self.fractions = {path: 0 for path in self.directories.keys()}

    def calc_fractions(self):
        self.fractions = CALC_FRACTIONS[self.active_mode](self.directories)

    def update(self, path: Path, directory: Directory):
        self.directories[path] = directory
        self.pending[path] = False
        self.calc_fractions()

    def set_active_mode(self, mode: str):
        self.active_mode = mode
        self.calc_fractions()
