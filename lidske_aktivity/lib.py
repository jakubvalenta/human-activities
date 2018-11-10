import stat
from pathlib import Path
from typing import Iterator


def _has_hidden_attribute(path: Path) -> bool:
    """See https://stackoverflow.com/a/6365265"""
    return bool(getattr(path.stat(), 'st_file_attributes', 0) &
                stat.FILE_ATTRIBUTE_HIDDEN)


def _is_hidden(path: Path) -> bool:
    return path.name.startswith('.') or _has_hidden_attribute(path)


def _list_dirs(path: Path) -> Iterator[Path]:
    return sorted(
        p for p in path.iterdir()
        if p.is_dir() and not _is_hidden(p)
    )


def list_home_dirs() -> Iterator[Path]:
    try:
        return _list_dirs(Path.home())
    except FileNotFoundError:
        return iter([])
