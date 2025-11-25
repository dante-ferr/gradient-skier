# -*- mode: python ; coding: utf-8 -*-
import os
import glob
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

src_path = os.path.abspath("src")
core_path = os.path.join(src_path, "core")

pathex_list = [
    src_path,
    core_path,
    os.path.join(core_path, "loaders"),
    os.path.join(core_path, "game"),
    os.path.join(core_path, "state_managers"),
]

ctk_datas = collect_data_files('customtkinter')

binaries_list = []
found_gtk = False

forced_path = os.environ.get('GTK_PATH_FORCE')

possible_paths = [
    r"C:\Program Files\GTK3-Runtime Win64\bin",
    r"C:\Program Files (x86)\GTK3-Runtime Win64\bin",
    r"C:\ProgramData\chocolatey\lib\gtk-runtime\tools\bin",
]

if forced_path:
    possible_paths.insert(0, forced_path)

for p in possible_paths:
    if os.path.exists(p) and os.path.isdir(p):
        dlls = glob.glob(os.path.join(p, "*.dll"))
        if dlls:
            for dll in dlls:
                binaries_list.append((dll, '.'))
            found_gtk = True
            break

a = Analysis(
    ['src/main.py'],
    pathex=pathex_list,
    binaries=binaries_list,
    datas=ctk_datas + [
        ('src/config.json', '.'),
        ('src/terrain_map/generator/generator_config.json', 'terrain_map/generator'),
        ('assets', 'assets')
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',
        'cairocffi',
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
    name='gradient-engineer',
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