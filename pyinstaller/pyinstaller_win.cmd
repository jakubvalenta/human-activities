pyinstaller ^
    --onefile ^
    --windowed ^
    --name=lidske-aktivity ^
    --specpath=pyinstaller ^
    --icon=data\lidske-aktivity.ico ^
    --hidden-import=sqlalchemy.ext.baked ^
    lidske_aktivity\__main__.py
