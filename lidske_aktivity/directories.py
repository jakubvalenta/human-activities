import csv
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
from typing import Callable, Dict, Optional, Sequence

from lidske_aktivity.utils import filesystem, math

logger = logging.getLogger(__name__)


@dataclass
class Directory:
    size: Optional[int] = None
    size_new: Optional[int] = None


TDirectories = Dict[Path, Directory]


def read_cached_directories(cache_path: Path) -> TDirectories:
    directories: TDirectories = {}
    if cache_path.is_file():
        with cache_path.open() as f:
            for row in csv.reader(f):
                if len(row) != 3:
                    continue
                path, size_raw, size_new_raw = row
                size = math.try_int(size_raw)
                if size is None:
                    continue
                size_new = math.try_int(size_new_raw)
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


def init_directories_from_root_path(cache_path: Path,
                                    root_path: Path) -> TDirectories:
    if not root_path.is_dir():
        logger.error('Path %s is not a directory', root_path)
        return {}
    paths = filesystem.list_dirs(root_path)
    directories = {path: Directory() for path in paths}
    return merge_directories(directories, read_cached_directories(cache_path))


def init_directories_from_paths(cache_path: Path,
                                paths: Sequence[Path] = ()) -> TDirectories:
    directories = {path: Directory() for path in paths}
    return merge_directories(directories, read_cached_directories(cache_path))


TScanCallback = Callable[[Path, Directory], None]


def scan_directory(path: Path,
                   callback: TScanCallback,
                   event_stop: Event,
                   test: bool = False):
    logger.info('Calculating size %s', path)
    thirty_days_ago = time.time() - 30 * 24 * 3600
    time_start = time.time()
    size, size_new = filesystem.calc_dir_size(
        str(path),
        threshold=thirty_days_ago,
        event_stop=event_stop
    )
    time_duration = time.time() - time_start
    logger.info(
        'Calculated size %s = %s (%s) in %f s',
        path,
        size,
        size_new,
        time_duration
    )
    if size is None or size_new is None:
        logger.warn('Size of %s is None, not using the result.', path)
        return
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
                     callback: TScanCallback,
                     event_stop: Event,
                     test: bool = False) -> Thread:
    def orchestrator():
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    scan_directory,
                    path,
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
