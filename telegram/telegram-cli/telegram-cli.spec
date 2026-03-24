# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Use os.getcwd() since __file__ may not be defined in spec context
PROJECT_DIR = Path(os.getcwd())
LIB_DIR = PROJECT_DIR.parent / 'telegram-lib'

a = Analysis(
    ['src/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        (str(PROJECT_DIR / 'src' / 'version.yaml'), 'src'),
        (str(LIB_DIR / 'telegram_lib' / 'version.yaml'), 'telegram_lib'),
    ],
    hiddenimports=['telegram_lib'],
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
    name='telegram-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
