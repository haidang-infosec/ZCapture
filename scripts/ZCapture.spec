# -*- mode: python ; coding: utf-8 -*-
import os

# PyInstaller automatically injects SPECPATH pointing to directory of this .spec file
ROOT_DIR = os.path.dirname(SPECPATH)

a = Analysis(
    [os.path.join(ROOT_DIR, 'main.py')],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=[
        (os.path.join(ROOT_DIR, 'core', 'zcapture_ocr.exe'), 'core'),
        (os.path.join(ROOT_DIR, 'core', 'ocr.cs'), 'core')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ZCapture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=os.path.join(ROOT_DIR, 'assets', 'version_info.txt'),
    icon=[os.path.join(ROOT_DIR, 'assets', 'app_icon.ico')],
)
