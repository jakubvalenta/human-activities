import logging
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase

from human_activities.utils.filesystem import find_files_fd, find_files_python

logging.basicConfig(level=logging.DEBUG)


class TestFilesystem(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        (Path(self.temp_dir) / 'foo').write_text('a')
        (Path(self.temp_dir) / 'bar').write_text('b')
        (Path(self.temp_dir) / 'Thumbs.db').write_text('c')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_find_files_fd_with_default_fdignore(self):
        result_paths = set(
            entry.path for entry in find_files_fd(self.temp_dir)
        )
        expected_paths = {
            str(Path(self.temp_dir) / 'foo'),
            str(Path(self.temp_dir) / 'bar'),
        }
        self.assertSetEqual(result_paths, expected_paths)

    def test_find_files_fd_with_custom_fdignore(self):
        with tempfile.NamedTemporaryFile('w+t') as temp_file:
            temp_file.write('bar')
            temp_file.seek(0)
            result_paths = set(
                entry.path
                for entry in find_files_fd(
                    self.temp_dir, fdignore_path=temp_file.name
                )
            )
            expected_paths = {
                str(Path(self.temp_dir) / 'foo'),
                str(Path(self.temp_dir) / 'Thumbs.db'),
            }
            self.assertSetEqual(result_paths, expected_paths)

    def test_find_files_python(self):
        result_paths = set(
            entry.path for entry in find_files_python(self.temp_dir)
        )
        expected_paths = {
            str(Path(self.temp_dir) / 'foo'),
            str(Path(self.temp_dir) / 'bar'),
        }
        self.assertSetEqual(result_paths, expected_paths)
