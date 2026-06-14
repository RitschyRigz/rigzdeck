# -*- mode: python ; coding: utf-8 -*-
# RigzDeck — PyInstaller-Spec (onedir, windowed/tray).
# Bauen:  pyinstaller --noconfirm RigzDeck.spec   (Frontend vorher: cd web && npm run build)
# Komfort: .\packaging\build.ps1  (baut Frontend + .exe in einem Rutsch)
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules("uvicorn")
    + collect_submodules("sse_starlette")
    + ["rigzdeck.app", "deckcore.service", "deckcore.api", "pystray._win32", "PIL"]
)

a = Analysis(
    ["rigzdeck_app.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("web/dist", "web/dist"),                       # gebautes Frontend (Editor + Panel)
        ("web/public/monogram-256.png", "assets"),      # Tray-Icon
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RigzDeck",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                                       # Tray-App, kein Konsolenfenster
    icon="web/public/monogram.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RigzDeck",
)
