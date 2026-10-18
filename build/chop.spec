# PyInstaller spec for Chop
from pathlib import Path

project_root = Path(SPECPATH).parent      
app_dir = project_root / "app"
resources = app_dir / "resources"

a = Analysis(
    [str(app_dir / "__main__.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[(str(resources / "icon.svg"), "app/resources")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="chop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="chop",
)
