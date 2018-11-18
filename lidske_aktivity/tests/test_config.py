from unittest import TestCase
from unittest import mock

from lidske_aktivity import config


APPDATA = r'C:\\Documents and Settings\\foo\\Application Data'
XDG_CACHE_HOME = '/home/foo/.cache'


class TestConfig(TestCase):

    @mock.patch('os.win32_ver', ('1',))
    @mock.patch.dict('os.environ', {'APPDATA': APPDATA})
    def test_win(self):
        self.assertEqual(
            config.get_cache_dir(),
            f'{APPDATA}/lidske-aktivity'
        )

    @mock.patch('os.win32_ver', ('1',))
    @mock.patch.dict('os.environ', {'APPDATA': ''})
    def test_win_fallback(self):
        self.assertEqual(
            config.get_cache_dir(),
            f'/home/foo/.cache/lidske-aktivity'
        )

    @mock.patch('os.mac_ver', ('1',))
    def test_mac(self):
        self.assertEqual(
            config.get_cache_dir(),
            f'/home/foo/Caches/org.example.lidske-aktivity'
        )

    @mock.patch.dict('os.environ', {'XDG_CACHE_HOME': XDG_CACHE_HOME})
    def test_linux(self):
        self.assertEqual(
            config.get_cache_dir(),
            f'{XDG_CACHE_HOME}/lidske-aktivity'
        )

    @mock.patch.dict('os.environ', {'XDG_CACHE_HOME': None})
    def test_linux_fallback(self):
        self.assertEqual(
            config.get_cache_dir(),
            f'{XDG_CACHE_HOME}/lidske-aktivity'
        )
