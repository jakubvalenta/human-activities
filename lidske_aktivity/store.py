import logging
import textwrap
from pathlib import Path
from threading import Event, Thread
from typing import Dict, List, NamedTuple, Optional, Tuple

from lidske_aktivity.bitmap import TColor, color_from_index
from lidske_aktivity.config import (
    CACHE_PATH, MODE_CUSTOM, MODE_HOME, MODE_NAMED, MODE_PATH, Config,
    TNamedDirs, load_config, save_config,
)
from lidske_aktivity.directories import (
    Directory, TDirectories, init_directories_from_paths,
    init_directories_from_root_path, scan_directories,
)
from lidske_aktivity.utils import math

logger = logging.getLogger(__name__)


class SizeMode(NamedTuple):
    name: str
    label: str
    tooltip: str


class ExtDirectory(NamedTuple):
    label: str
    color: TColor
    fraction: Optional[float] = 0
    percent: Optional[float] = 0
    pending: bool = True
    tooltip: str = ''


TExtDirectories = Dict[Path, ExtDirectory]
TFractions = Dict[Path, float]

SIZE_MODE_SIZE = 'size'
SIZE_MODE_SIZE_NEW = 'size_new'
SIZE_MODES = (
    SizeMode(
        name=SIZE_MODE_SIZE,
        label='by size',
        tooltip='Compares data size of the directories.'
    ),
    SizeMode(
        name=SIZE_MODE_SIZE_NEW,
        label='by activity',
        tooltip=('Shows how many percent of the files in each directory '
                 'was modified in the past 30 days.')
    ),
)

TOOLTIPS = {
    SIZE_MODE_SIZE: '{:.2%} of the size of all configured directories',
    SIZE_MODE_SIZE_NEW: (
        '{:.2%} of the files in this directory was modified in the past 30'
        'days'
    )
}


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


def format_label(path: str, config_mode: str, named_dirs: TNamedDirs) -> str:
    if (config_mode == MODE_NAMED and path in named_dirs):
        return named_dirs[path]
    return path.name


def format_tooltip(fraction: float, active_mode: str):
    s = TOOLTIPS[active_mode].format(fraction)
    return textwrap.fill(s)


def load_directories(config: Config) -> TDirectories:
    init_funcs = {
        MODE_HOME: lambda: init_directories_from_root_path(
            CACHE_PATH, Path.home()
        ),
        MODE_PATH: lambda: init_directories_from_root_path(
            CACHE_PATH, config.root_path
        ),
        MODE_CUSTOM: lambda: init_directories_from_paths(
            CACHE_PATH, config.custom_dirs
        ),
        MODE_NAMED: lambda: init_directories_from_paths(
            CACHE_PATH, config.named_dirs.keys()
        )
    }
    init_func = init_funcs[config.mode]
    return init_func()


class Store:
    _config: Config
    _directories: TDirectories
    ext_directories: TExtDirectories
    _active_mode: str = SIZE_MODE_SIZE

    scan_event_stop: Optional[Event] = None
    scan_thread: Thread
    last_percents: Optional[TFractions] = None

    def __init__(self):
        self.config = load_config()

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, config: Config):
        self._config = config
        save_config(config)
        self._init()

    def _init(self):
        self._scan_stop()
        self._directories = load_directories(self._config)
        self._create_ext_directories()
        self._scan_start()

    def _scan_start(self):
        self.scan_event_stop = Event()
        self.scan_thread = scan_directories(
            self._directories,
            cache_path=CACHE_PATH,
            callback=self._update_directory,
            event_stop=self.scan_event_stop,
            test=self.config.test
        )

    def _scan_stop(self):
        if self.scan_event_stop:
            self.scan_event_stop.set()
            self.scan_thread.join()
            logger.info('Scan stopped')

    def _create_ext_directories(self):
        self.ext_directories = {
            path: ExtDirectory(
                label=format_label(
                    path,
                    self.config.mode,
                    self.config.named_dirs
                ),
                color=color_from_index(i)
            )
            for i, (path, directory) in enumerate(self._directories.items())
        }

    def _update_ext_directories(self):
        calc_funcs = {
            SIZE_MODE_SIZE: calc_size,
            SIZE_MODE_SIZE_NEW: calc_size_new,
        }
        calc_func = calc_funcs[self.active_mode]
        fractions, percents = calc_func(self._directories)
        self.ext_directories = {
            path: ext_directory._replace(
                fraction=fractions[path],
                percent=percents[path],
                tooltip=format_tooltip(fractions[path], self.active_mode),
            )
            for path, ext_directory in self.ext_directories.items()
        }

    @property
    def active_mode(self):
        return self._active_mode

    @active_mode.setter
    def active_mode(self, mode: str):
        self._active_mode = mode
        self._update_ext_directories()

    def _update_directory(self, path: Path, directory: Directory):
        self._directories[path] = self._directories[path]._replace(
            size=directory.size,
            size_new=directory.size_new,
        )
        self._update_ext_directories()
        self.ext_directories[path] = self.ext_directories[path]._replace(
            pending=False
        )

    @property
    def tooltip(self):
        return '\n'.join(
            f'{ext_directory.label}: {ext_directory.fraction:.2%}'
            for ext_directory in self.ext_directories.values()
        )

    @property
    def percents(self) -> List[float]:
        return [
            ext_directory.percent
            for ext_directory in self.ext_directories.values()
        ]
