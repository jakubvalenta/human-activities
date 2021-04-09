# -*- mode: python -*-

import os.path

block_cipher = None

a = Analysis(  # noqa: F821
    [os.path.join('..', 'human_activities', '__main__.py')],
    pathex=['mac'],
    binaries=[],
    datas=[
        (
            os.path.join('..', 'human_activities', 'locale'),
            os.path.join('locale'),
        ),
        (
            os.path.join('..', 'human_activities', 'qt', 'data', '__init__.py'),
            os.path.join('human_activities', 'qt', 'data'),
        ),
        (
            os.path.join('..', 'human_activities', 'qt', 'data', 'qt_wizard_bg.png'),
            os.path.join('human_activities', 'qt', 'data'),
        ),
        (
            os.path.join('..', 'human_activities', 'etc', '__init__.py'),
            os.path.join('human_activities', 'etc'),
        ),
        (
            os.path.join('..', 'human_activities', 'etc', 'human-activities.fdignore'),
            os.path.join('human_activities', 'etc'),
        ),
    ],
    hiddenimports=[
        'sqlalchemy.ext.baked',
        'sqlalchemy.sql.default_comparator',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='human-activities',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
)
app = BUNDLE(  # noqa: F821
    exe,
    name='Human Activities.app',
    icon=os.path.join('..', 'data', 'human-activities.icns'),
    bundle_identifier='cz.jakubvalenta.human-activities',
    info_plist={
        'NSPrincipleClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'LSUIElement': '1',
    },
)
