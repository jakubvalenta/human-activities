import logging
import textwrap
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, wait
from threading import Event, Thread
from typing import Callable, Dict, Optional, Sequence

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from lidske_aktivity.config import (
    VALUE_NAME_NUM_FILES, VALUE_NAME_SIZE_BYTES, VALUE_NAMES, Config,
    TNamedDirs, load_config, save_config,
)
from lidske_aktivity.utils import filesystem, func, math

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine('sqlite:///:memory:')  # TODO: echo=True
Session = sessionmaker(bind=engine)
session = Session()


class Stat(Base):  # type: ignore
    __tablename__ = 'stats'

    id = Column(Integer, primary_key=True)
    size_bytes = Column(Integer)
    num_files = Column(Integer)
    threshold_days_ago = Column(Integer, nullable=False)
    directory_id = Column(Integer, ForeignKey('directories.id'))
    directory = relationship('Directory', back_populates='stats')

    fractions: Dict[str, float]

    def __repr__(self) -> str:
        return (f'Stat(size_bytes={self.size_bytes}, '
                f'num_files={self.num_files}, '
                f'threshold_days_ago={self.threshold_days_ago})')


TScanCallback = Callable[['Directory'], None]


class Directory(Base):  # type: ignore
    __tablename__ = 'directories'

    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False, unique=True)
    stats = relationship('Stat', back_populates='directory')

    label: str = ''
    pending: bool = False

    @func.measure_time
    def scan(self,
             callback: TScanCallback,
             event_stop: Event,
             threshold_days_ago: int,
             test: bool = False):
        logger.info('Calculating size of "%s"', self.path)
        self.pending = True
        threshold_seconds_ago = threshold_days_ago * 24 * 3600
        threshold_seconds = time.time() - threshold_seconds_ago
        dir_size = filesystem.calc_dir_size(
            self.path,
            threshold_seconds=threshold_seconds,
            event_stop=event_stop
        )
        self.stats = [
            Stat(
                size_bytes=dir_size.size_bytes_all,
                num_files=dir_size.num_files_all,
                threshold_days_ago=0
            )
        ]
        if threshold_days_ago != 0:
            self.stats.append(
                Stat(
                    size_bytes=dir_size.size_bytes_new,
                    num_files=dir_size.num_files_new,
                    threshold_days_ago=threshold_days_ago
                )
            )
        if test:
            func.random_wait(event_stop)
        self.pending = False
        logger.info('Calculated size of "%s": %s', self.path, self.stats)
        callback(self)

    def __repr__(self) -> str:
        return (f'Directory(path={self.path}, label={self.label}, '
                f'stats={self.stats})')


Base.metadata.create_all(engine)


class DirectoryView:
    directory: Directory
    _value_name: str
    _threshold_days_ago: int

    fraction: float
    text: str
    tooltip: str

    def __init__(self,
                 directory: Directory,
                 value_name: str,
                 threshold_days_ago: int):
        self.directory = directory
        self._value_name = value_name
        self._threshold_days_ago = threshold_days_ago

        self.fraction = self._get_fraction()
        self.text = self._get_text()
        self.tooltip = self._get_tooltip()

    def _get_text(self) -> str:
        if self.directory.pending:
            return f'{self.directory.label}: ...'
        return f'{self.directory.label}: {self.fraction:.0%}'

    def _get_tooltip(self) -> str:
        value_text = {
            VALUE_NAME_SIZE_BYTES: 'of the size ',
            VALUE_NAME_NUM_FILES: '',
        }[self._value_name]
        if self._threshold_days_ago == 0:
            set_text = 'all files in configured directories'
        else:
            set_text = (f'the files modified in the past '
                        f'{self._threshold_days_ago} days')
        s = f'{self.fraction:.2%} {value_text}of {set_text}'
        return textwrap.fill(s)

    def _get_fraction(self) -> float:
        for stat in self.directory.stats:
            if stat.threshold_days_ago == self._threshold_days_ago:
                return stat.fractions[self._value_name]
        return 0

    def __repr__(self) -> str:
        return (f'DirectoryView(directory={self.directory.path}, '
                f'fraction={self.fraction}, value_name={self._value_name}, '
                f'threshold_days_ago={self._threshold_days_ago})')


class Directories(list):
    _scan_event_stop: Optional[Event] = None
    _scan_thread: Thread

    def __init__(self,
                 configured_dirs: TNamedDirs,
                 on_scan: Callable,
                 threshold_days_ago: int,
                 test: bool = False):
        """Create directories for all paths, load from cache if available."""
        super().__init__()
        self._on_scan = on_scan
        paths = list(configured_dirs.values())
        query = (
            session.query(Directory)
            .filter(Directory.path.in_(paths))
            .order_by(Directory.path)
        )
        directories_dict = {
            directory.path: directory
            for directory in query
        }
        for path, label in configured_dirs.items():
            if path in directories_dict:
                directory = directories_dict[path]
            else:
                directory = Directory(path=path)
            directory.label = label
            logger.info('Created %s', directory)
            self.append(directory)
        self._scan_start(threshold_days_ago, test=test)

    def save(self):
        session.add_all(self)

    def _scan_start(self, threshold_days_ago: int, test: bool = False):
        self._scan_event_stop = Event()

        def orchestrator():
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(
                        directory.scan,
                        self._on_directory_scanned,
                        self._scan_event_stop,
                        threshold_days_ago,
                        test
                    )
                    for directory in self
                ]
                wait(futures)
                self.save()

        self._scan_thread = Thread(target=orchestrator)
        self._scan_thread.start()

    def scan_stop(self):
        if self._scan_event_stop:
            self._scan_event_stop.set()
            self._scan_thread.join()
            logger.info('Scan stopped')

    def _on_directory_scanned(self, directory: Directory):
        total: Dict[str, Dict[int, int]] = {
            value_name: defaultdict(int)
            for value_name in VALUE_NAMES
        }
        for directory in self:
            for stat in directory.stats:
                for value_name in total:
                    value = getattr(stat, value_name)
                    total[value_name][stat.threshold_days_ago] += value
        for directory in self:
            for stat in directory.stats:
                stat.fractions = {
                    value_name: math.safe_div(
                        getattr(stat, value_name),
                        total[value_name][stat.threshold_days_ago]
                    )
                    for value_name in total
                }
        self._on_scan()


class Model:
    _config: Config
    _directories: Optional[Directories] = None
    _directory_views: Sequence[DirectoryView] = ()

    def __init__(self):
        # Use the config setter to immediatelly trigger config saving.
        self.config = load_config()

    @property
    def config(self) -> Config:
        return self._config

    @config.setter
    def config(self, config: Config):
        self._config = config
        save_config(config)
        self.scan_stop()
        self._directories = Directories(
            self._config.configured_dirs,
            self._update_directory_views,
            self._config.threshold_days_ago,
            test=self._config.test
        )

    @property
    def directory_views(self) -> Sequence[DirectoryView]:
        return self._directory_views

    def _update_directory_views(self):
        self._directory_views = [
            DirectoryView(
                directory,
                self._config.value_name,
                self._config.threshold_days_ago
            )
            for directory in self._directories
        ]

    def scan_stop(self):
        if self._directories:
            self._directories.scan_stop()
