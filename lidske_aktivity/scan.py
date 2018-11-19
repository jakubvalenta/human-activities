import csv
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
from typing import Any, Callable, Dict, Optional

from lidske_aktivity import filesystem

logger = logging.getLogger(__name__)


@dataclass
class Directory:
    size: Optional[int] = None
    size_new: Optional[int] = None


TDirectories = Dict[Path, Directory]
TPending = Dict[Path, bool]
TCallback = Callable[[Path, Directory], None]
TFractions = Dict[Path, float]


@dataclass
class SizeMode:
    label: str
    calc_fractions: Callable[[TDirectories], TFractions]


def safe_div(a: int, b: int) -> float:
    if a and b:
        return a / b
    return 0


def calc_size_fractions(directories: TDirectories) -> TFractions:
    total_size = sum(d.size or 0 for d in directories.values())
    return {
        path: safe_div(directory.size, total_size)
        for path, directory in directories.items()
    }


def calc_size_new_fractions(directories: TDirectories) -> TFractions:
    return {
        path: safe_div(directory.size_new, directory.size)
        for path, directory in directories.items()
    }


SIZE_MODES = {
    'size': SizeMode('by size', calc_size_fractions),
    'size_new': SizeMode('by acitivty', calc_size_new_fractions),
}


def read_directories(root_path: Path) -> TDirectories:
    return {path: Directory() for path in filesystem.list_dirs(root_path)}


def try_int(val: Any) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def read_cached_directories(cache_path: Path) -> TDirectories:
    directories: TDirectories = {}
    if cache_path.is_file():
        with cache_path.open() as f:
            for row in csv.reader(f):
                if len(row) != 3:
                    continue
                path, size_raw, size_new_raw = row
                size = try_int(size_raw)
                if size is None:
                    continue
                size_new = try_int(size_new_raw)
                if size_new is None:
                    continue
                directories[Path(path)] = Directory(
                    size=size,
                    size_new=size_new,
                )
    return directories


def write_cache(cache_path: Path, directories: TDirectories):
    logger.info('Writing cache')
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open('w') as f:
        writer = csv.writer(f)
        writer.writerows(
            (str(path), d.size, d.size_new)
            for path, d in directories.items()
            if path and d.size is not None and d.size_new is not None
        )


def merge_directories(a: TDirectories, b: TDirectories) -> TDirectories:
    if not a or not b:
        return a
    return {
        path: b.get(path, d)
        for path, d in a.items()
    }


def init_directories(cache_path: Path,
                     root_path: Path = Path.home()) -> TDirectories:
    if not root_path.is_dir():
        logger.error('Path %s is not a directory', root_path)
        return {}
    return merge_directories(
        read_directories(root_path),
        read_cached_directories(cache_path),
    )


def scan_directory(path: Path,
                   directories: TDirectories,
                   callback: TCallback,
                   event_stop: Event,
                   test: bool = False):
    logger.info('Calculating size %s', path)
    thirty_days_ago = time.time() - 30 * 24 * 3600
    time_start = time.time()
    size, size_new = filesystem.calc_dir_size(
        str(path),
        thirty_days_ago,
        event_stop
    )
    time_duration = time.time() - time_start
    logger.info(
        'Calculated size %s = %d (%d) in %f s',
        path,
        size,
        size_new,
        time_duration
    )
    if test:
        for _ in range(random.randint(1, 20)):
            if event_stop.is_set():
                logger.warn('Stopping test sleep')
                break
            time.sleep(1)
    directory = Directory(size=size, size_new=size_new)
    callback(path, directory)


def scan_directories(directories: TDirectories,
                     cache_path: Path,
                     callback: TCallback,
                     event_stop: Event,
                     test: bool = False) -> Thread:
    def orchestrator():
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    scan_directory,
                    path,
                    directories,
                    callback,
                    event_stop,
                    test
                )
                for path in directories.keys()
            ]
            wait(futures)
            write_cache(cache_path, directories)
    thread = Thread(target=orchestrator)
    thread.start()
    return thread
