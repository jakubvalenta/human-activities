import logging
import tempfile
from pathlib import Path
from unittest import TestCase

from human_activities.utils.filesystem import scan_dir

logging.basicConfig(level=logging.DEBUG)


class TestFilesystem(TestCase):
    def test_scan_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / 'foo').write_text('foo')
            (Path(temp_dir) / 'bar').write_text('bar')
            result_paths = set(entry.path for entry in scan_dir(temp_dir))
            expected_paths = {
                str(Path(temp_dir) / 'foo'),
                str(Path(temp_dir) / 'bar'),
            }
            self.assertSetEqual(result_paths, expected_paths)
