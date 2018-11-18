from pathlib import PurePosixPath, PureWindowsPath
from unittest import TestCase, mock

from lidske_aktivity import config

WIN_HOME = PureWindowsPath(r'C:\Documents and Settings\foo')
MAC_HOME = PurePosixPath('/Users/foo')
LINUX_HOME = PurePosixPath('/home/foo')
WIN_APPDATA = WIN_HOME / 'Application Data'
XDG_CACHE_HOME = LINUX_HOME / '.cache'


@mock.patch('platform.win32_ver', lambda: ('1',))
@mock.patch('platform.mac_ver', lambda: (None,))
@mock.patch('pathlib.Path.home', lambda: WIN_HOME)
class TestConfigWin(TestCase):

    @mock.patch.dict('os.environ', {'APPDATA': str(WIN_APPDATA)})
    def test_win(self):
        self.assertEqual(
            config.get_cache_dir(),
            WIN_APPDATA / 'lidske-aktivity'
        )

    @mock.patch.dict('os.environ', {'APPDATA': ''})
    def test_win_fallback(self):
        self.assertEqual(
            config.get_cache_dir(),
            WIN_HOME / '.cache' / 'lidske-aktivity'
        )


@mock.patch('platform.win32_ver', lambda: (None,))
@mock.patch('platform.mac_ver', lambda: ('1',))
@mock.patch('pathlib.Path.home', lambda: MAC_HOME)
class TestConfigMac(TestCase):

    def test_mac(self):
        self.assertEqual(
            config.get_cache_dir(),
            MAC_HOME / 'Caches' / 'com.example.lidske-aktivity'
        )


@mock.patch('platform.win32_ver', lambda: (None,))
@mock.patch('platform.mac_ver', lambda: (None,))
@mock.patch('pathlib.Path.home', lambda: LINUX_HOME)
class TestConfigLinux(TestCase):

    @mock.patch.dict('os.environ', {'XDG_CACHE_HOME': str(XDG_CACHE_HOME)})
    def test_linux(self):
        self.assertEqual(
            config.get_cache_dir(),
            XDG_CACHE_HOME / 'lidske-aktivity'
        )

    @mock.patch.dict('os.environ', {'XDG_CACHE_HOME': ''})
    def test_linux_fallback(self):
        self.assertEqual(
            config.get_cache_dir(),
            XDG_CACHE_HOME / 'lidske-aktivity'
        )
