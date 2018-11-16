import csv
import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from threading import Thread
from typing import Callable, Dict, Optional

from lidske_aktivity.filesystem import calc_dir_size, list_dirs

logger = logging.getLogger(__name__)

TDirectories = Dict[Path, int]
TCallback = Callable[[TDirectories], None]


def sum_size(directories: TDirectories) -> int:
    return sum(size or 0 for size in directories.values())


def read_directories(root_path: Path) -> TDirectories:
    return {path: None for path in list_dirs(root_path)}


def try_int(val: any) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def read_cached_directories(cache_path: Path) -> TDirectories:
    directories = {}
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


def write_cache(cache_path: Path, directories: TDirectories) -> None:
    logger.warn('Writing cache')
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
                     root_path: Optional[Path] = Path.home()) -> TDirectories:
    if not root_path.is_dir():
        logger.error('Path %s is not a directory', root_path)
        return {}
    return merge_directories(
        read_directories(root_path),
        read_cached_directories(cache_path),
    )


def random_wait():
    time.sleep(random.randint(1, 20))


def scan_directory(path: Path,
                   directories: TDirectories,
                   callback: TCallback,
                   test: bool = False):
    directories[path] = calc_dir_size(path)
    if test:
        random_wait()
    callback(directories)


def scan_directories(directories: TDirectories,
                     cache_path: Path,
                     callback: TCallback,
                     test: bool = False) -> None:
    def func():
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    scan_directory,
                    path,
                    directories,
                    callback,
                    test
                )
                for path in directories.keys()
            ]
            wait(futures)
            write_cache(cache_path, directories)
    thread = Thread(target=func)
    thread.start()
