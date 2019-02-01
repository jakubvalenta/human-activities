# -*- mode: python -*-

import os.path

block_cipher = None

a = Analysis(  # noqa: F821
    [os.path.join('..', 'lidske_aktivity', '__main__.py')],
    pathex=['linux_pyinstaller'],
    binaries=[],
    datas=[(
        os.path.join('..', 'lidske_aktivity', 'locale'),
        os.path.join('locale')
    )],
    hiddenimports=['sqlalchemy.ext.baked'],
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
    console=False,
    icon=os.path.join('data', 'lidske-aktivity.ico')
)
