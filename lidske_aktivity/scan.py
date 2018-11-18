import csv
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from threading import Event, Thread
from typing import Any, Callable, Dict, Optional

from lidske_aktivity import filesystem

logger = logging.getLogger(__name__)

TDirectories = Dict[Path, Optional[int]]
TPending = Dict[Path, bool]
TCallback = Callable[[Path, Optional[int]], None]


def sum_size(directories: TDirectories) -> int:
    return sum(size or 0 for size in directories.values())


def read_directories(root_path: Path) -> TDirectories:
    return {path: None for path in filesystem.list_dirs(root_path)}


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
                if len(row) != 2:
                    continue
                path, size_raw = row
                size = try_int(size_raw)
                if size is None:
                    continue
                directories[Path(path)] = size
    return directories


def write_cache(cache_path: Path, directories: TDirectories):
    logger.info('Writing cache')
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open('w') as f:
        writer = csv.writer(f)
        writer.writerows(
            (str(path), size)
            for path, size in directories.items()
            if path and size is not None
        )


def merge_directories(a: TDirectories, b: TDirectories) -> TDirectories:
    if not a or not b:
        return a
    return {
        path: b.get(path, size)
        for path, size in a.items()
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
    time_start = time.time()
    size = filesystem.calc_dir_size(str(path), event_stop)
    time_duration = time.time() - time_start
    logger.info('Calculated size %s = %d in %f s', path, size, time_duration)
    if test:
        for _ in range(random.randint(1, 20)):
            if event_stop.is_set():
                logger.warn('Stopping test sleep')
                break
            time.sleep(1)
    callback(path, size)


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
