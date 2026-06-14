# RigzDeck Build — Frontend bauen + .exe paketieren (PyInstaller).
# Aufruf aus dem Repo-Root:  .\packaging\build.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> Frontend bauen (web/)..." -ForegroundColor Cyan
Set-Location "$root\web"
if (-not (Test-Path "node_modules")) { npm install }
npm run build
Set-Location $root

Write-Host "==> Build-/Desktop-Abhaengigkeiten sicherstellen..." -ForegroundColor Cyan
python -m pip install -r requirements.txt -r requirements-build.txt

Write-Host "==> PyInstaller..." -ForegroundColor Cyan
# `python -m PyInstaller` statt blankem `pyinstaller` — der Scripts-Ordner liegt nicht
# zwangslaeufig auf der PATH (pip warnt beim Install), das Modul findet Python immer.
python -m PyInstaller --noconfirm RigzDeck.spec

Write-Host ""
Write-Host "==> Fertig: dist\RigzDeck\RigzDeck.exe" -ForegroundColor Green
Write-Host "    Installer (optional): Inno Setup -> ISCC.exe packaging\RigzDeck.iss"
