import logging
import os
import time
import traceback
from threading import Event
from typing import Callable, Iterable, NamedTuple, Optional, Tuple

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.orm.session import Session

from lidske_aktivity import CACHE_PATH
from lidske_aktivity.config import UNIT_SIZE_BYTES, TNamedDirs
from lidske_aktivity.locale import _
from lidske_aktivity.utils import filesystem, func
from lidske_aktivity.utils.math import safe_div

logger = logging.getLogger(__name__)

Base = declarative_base()


class Stat(Base):  # type: ignore
    __tablename__ = 'stats'

    id = Column(Integer, primary_key=True)
    size_bytes = Column(Integer)
    num_files = Column(Integer)
    threshold_days_ago = Column(Integer, nullable=False)
    directory_id = Column(Integer, ForeignKey('directories.id'))
    directory = relationship('Directory', back_populates='stats')

    def __repr__(self) -> str:
        return (
            f'Stat(size_bytes={self.size_bytes}, '
            f'num_files={self.num_files}, '
            f'threshold_days_ago={self.threshold_days_ago})'
        )


class Directory(Base):  # type: ignore
    __tablename__ = 'directories'

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False, unique=True)
    stats = relationship(
        'Stat',
        back_populates='directory',
        cascade='all, delete, delete-orphan',
    )

    def find_value(self, unit: str, threshold_days_ago: int) -> Optional[int]:
        for stat in self.stats:
            if stat.threshold_days_ago == threshold_days_ago:
                return getattr(stat, unit)
        return None

    def __repr__(self) -> str:
        return f'Directory(path={self.path}, stats={self.stats})'


def create_database_engine():
    engine = create_engine(f'sqlite:///{CACHE_PATH}')
    Base.metadata.create_all(engine)
    return engine


try:
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    engine = create_database_engine()
except DatabaseError:
    os.remove(CACHE_PATH)
    engine = create_database_engine()
session_factory = sessionmaker(bind=engine)


class Directories(list):
    _session: Session

    def __init__(self):
        self._session = scoped_session(session_factory)

    def load_from_db(self, paths: Iterable[str]):
        query = (
            self._session.query(Directory)
            .filter(Directory.path.in_(paths))
            .order_by(Directory.path)
        )
        for directory in query:
            logger.info('DB: Loaded %s', directory)
            self.append(directory)

    def create_missing(self, paths: Iterable[str]):
        existing_paths = [directory.path for directory in self]
        for path in paths:
            if path in existing_paths:
                continue
            directory = Directory(path=path)
            logger.info('DB: Inserting %s', directory)
            self._session.add(directory)
            self.append(directory)

    def clear(self):
        for directory in self:
            logger.info('DB: Deleting %s', directory)
            self._session.delete(directory)
        super().clear()

    def save(self):
        self._session.commit()

    def __del__(self):
        self._session.close()


class DirectoryView(NamedTuple):
    label: str
    unit: str
    threshold_days_ago: int
    value: Optional[float] = None
    fraction: Optional[float] = None
    pending: bool = True

    @property
    def text(self):
        s = f'{self.label}: '
        if self.value is not None:
            s += f'{self.fraction:.0%} ({self.value_str})'
        if self.pending:
            s += '\N{HORIZONTAL ELLIPSIS}'
        elif self.value is None:
            s += 'n/a'
        return s

    @property
    def value_str(self) -> str:
        if self.unit == UNIT_SIZE_BYTES:
            return filesystem.humansize(self.value or 0)
        return _('{value} files').format(value=self.value)


class DirectoryViews(dict):
    unit: str
    threshold_days_ago: int = 0

    def config(
        self, unit: str, threshold_days_ago: int, named_dirs: TNamedDirs
    ):
        self.unit = unit
        self.threshold_days_ago = threshold_days_ago
        self.clear()
        for path, label in named_dirs.items():
            self[path] = DirectoryView(
                label=label, unit=unit, threshold_days_ago=threshold_days_ago
            )

    def load(self, *directories: Directory, **extra_props):
        for directory in directories:
            if directory.path not in self:
                logger.error(
                    'Directory view for path %s doesn\'t exist', directory.path
                )
                continue
            value = directory.find_value(self.unit, self.threshold_days_ago)
            self[directory.path] = self[directory.path]._replace(
                value=value, **extra_props
            )
        total = sum(dv.value or 0.0 for dv in self.values())
        for path, directory_view in self.items():
            fraction = round(safe_div(directory_view.value, total), 2)
            if directory_view.fraction != fraction:
                self[path] = directory_view._replace(fraction=fraction)
        logger.info('Recalculated: fractions = %s', self.fractions)

    @property
    def fractions(self) -> Tuple[float, ...]:
        return tuple(dv.fraction or 0.0 for dv in self.values())

    @property
    def tooltip(self) -> str:
        return '\n'.join(dv.text for dv in self.values())

    def copy(self) -> 'DirectoryViews':
        new = DirectoryViews()
        new.unit = self.unit
        new.threshold_days_ago = self.threshold_days_ago
        new.update(self)
        return new


@func.measure_time
def scan_directory(
    path: str,
    unit: str,
    threshold_days_ago: int,
    event_stop: Event,
    callback: Callable[[Directory], None],
    test: bool = False,
):
    logger.info('Scanning "%s"', path)
    try:
        session = scoped_session(session_factory)
        directory = (
            session.query(Directory).filter(Directory.path == path).one()
        )
        threshold_seconds_ago = threshold_days_ago * 24 * 3600
        threshold_seconds = time.time() - threshold_seconds_ago
        dir_size = filesystem.calc_dir_size(
            directory.path,
            threshold_seconds=threshold_seconds,
            event_stop=event_stop,
        )
        directory.stats.clear()
        directory.stats.append(
            Stat(
                size_bytes=dir_size.size_bytes_all,
                num_files=dir_size.num_files_all,
                threshold_days_ago=0,
            )
        )
        if threshold_days_ago != 0:
            directory.stats.append(
                Stat(
                    size_bytes=dir_size.size_bytes_new,
                    num_files=dir_size.num_files_new,
                    threshold_days_ago=threshold_days_ago,
                )
            )
        if test:
            func.random_wait(event_stop)
        logger.info('Scanned "%s": %s', directory.path, directory.stats)
        logger.info('DB: Updating %s', directory)
        session.commit()
        callback(directory)
    except Exception:
        logger.error('Exception while scanning "%s"', path)
        logger.info(traceback.format_exc())
    finally:
        session.close()


def clean_cache():
    if CACHE_PATH.is_file():
        CACHE_PATH.unlink()
        logger.info('Removed cache file %s', CACHE_PATH)
    else:
        logger.info('Nothing to do, cache file %s doesn\'t exist', CACHE_PATH)
