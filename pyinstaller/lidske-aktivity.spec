# -*- mode: python -*-

block_cipher = None


a = Analysis(  # noqa: F821
    ['../lidske_aktivity/__main__.py'],
    pathex=['install'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(  # noqa: F821
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='lidske-aktivity',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False
)
app = BUNDLE(  # noqa: F821
    exe,
    name='lidske-aktivity.app',
    icon=None,
    bundle_identifier=None,
    info_plist={
        'NSPrincipleClass': 'NSApplication',
        'NSAppleScriptEnabled': False
    }
)
