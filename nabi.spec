# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Nabi v3.0.0

import os

block_cipher = None

a = Analysis(
    ['nabi_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/avatars', 'assets/avatars'),
        ('assets/backgrounds', 'assets/backgrounds'),
        ('assets/sounds', 'assets/sounds'),
        ('assets/icon.png', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Nabi',
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
    icon='assets/icon.ico',
    codesign_identity=None,
    entitlements_file=None,
)
