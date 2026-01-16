# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for YT-DLP GUI
Build with: pyinstaller yt-dlp-gui.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Get the source directory
src_dir = Path('src')

a = Analysis(
    ['src/main.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        ('yt-dlp.exe', '.'),  # Include yt-dlp executable
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'yt_dlp',
        'PIL',
        'requests',
    ],
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
    name='yt-dlp-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
