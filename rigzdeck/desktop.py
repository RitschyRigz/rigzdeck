"""RigzDeck desktop launcher — runs the FastAPI server in a background thread and lives in
the Windows system tray (open editor/panel, copy the LAN URL for tablets, quit).

This is the entry point the packaged .exe uses (see ``RigzDeck.spec`` / ``rigzdeck_app.py``);
``python -m rigzdeck`` stays the plain headless server. pystray/Pillow are imported lazily,
so importing this module doesn't require them — only ``main()`` does.
"""
from __future__ import annotations

import socket
import subprocess
import sys
import threading
import webbrowser
import winreg
from pathlib import Path

import uvicorn

from .app import create_app, PORT


def _lan_ip() -> str:
    """Beste lokale LAN-IP (für die Tablet-URL); Fallback 127.0.0.1."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class _Server:
    """uvicorn in einem Hintergrund-Thread; sauber stoppbar über ``should_exit``."""

    def __init__(self, port: int = PORT):
        self.port = port
        cfg = uvicorn.Config(create_app(), host="0.0.0.0", port=port, log_level="warning")
        self._server = uvicorn.Server(cfg)
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)


def _tray_image():
    """Tray-Icon laden (gebündelt unter ``assets/`` bzw. neben dem Modul); Fallback = Akzent-Quadrat."""
    from PIL import Image
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for cand in (base / "assets" / "monogram-256.png",
                 base / "monogram-256.png",
                 base.parent / "web" / "public" / "monogram-256.png"):
        try:
            if cand.exists():
                return Image.open(cand)
        except Exception:
            pass
    return Image.new("RGB", (64, 64), (138, 92, 255))


def _copy_to_clipboard(text: str) -> None:
    try:
        subprocess.run(["clip"], input=text.encode("utf-8"), check=False,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception:
        pass


def _open_window(url: str) -> None:
    """Öffnet die URL in einem sauberen App-Fenster (Edge/Chrome ``--app``: keine Adressleiste,
    keine Tabs, kein Browser-Rahmen, eigenes Icon). Fällt auf den Standardbrowser zurück."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    exe = next((c for c in candidates if Path(c).exists()), None)
    if exe:
        try:
            subprocess.Popen([exe, f"--app={url}"])
            return
        except Exception:
            pass
    webbrowser.open(url)


# ── Single-Instance-Sperre (Named Mutex) — verhindert eine 2. Instanz ────────────
_MUTEX_HANDLE = None   # prozessweit gehalten, solange RigzDeck läuft


def _already_running() -> bool:
    """True, wenn bereits eine RigzDeck-Instanz läuft. ZWEI robuste Checks (ODER):
      (1) **Named Mutex** (atomar) → fängt den gleichzeitigen Boot-Start zweier Launcher ab, BEVOR
          überhaupt jemand den Port bindet.
      (2) **Port-Probe** auf 7990 → fängt ALLES ab, was den Port schon hält (eine bereits laufende
          Instanz, eine ALTE Version ohne Mutex, ein headless `python -m rigzdeck`). Damit startet nie
          ein zweiter Server → kein `[Errno 10048]`-Bind-Fehler + kein mDNS-Spam mehr.
    Konservativ False bei Fehlern (lieber starten als gar nicht)."""
    return _mutex_taken() or _port_in_use(PORT)


def _mutex_taken() -> bool:
    """Named-Mutex-Check — ZUVERLÄSSIG via ``use_last_error=True`` + ``ctypes.get_last_error()``
    (das blanke ``windll.kernel32.GetLastError()`` ist in ctypes unzuverlässig: ctypes kann den
    Fehlercode zwischen den Calls zurücksetzen → mal greift die Sperre, mal nicht)."""
    global _MUTEX_HANDLE
    try:
        import ctypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _MUTEX_HANDLE = k32.CreateMutexW(None, False, "RigzDeck_SingleInstance")
        return ctypes.get_last_error() == 183   # ERROR_ALREADY_EXISTS
    except Exception:
        return False


def _port_in_use(port: int) -> bool:
    """True, wenn auf 127.0.0.1:<port> schon jemand lauscht (laufende RigzDeck-Instanz)."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        return s.connect_ex(("127.0.0.1", int(port))) == 0
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


# ── Autostart mit Windows (HKCU\…\Run — pro Benutzer, kein Admin) — 3 Modi: off/tray/window ──
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_NAME = "RigzDeck"


def _autostart_command(window: bool) -> str:
    """Login-Befehl. ``window=False`` → still in den Tray (``--autostart``); ``window=True`` → mit
    Fenster (kein Flag → öffnet den Editor). Im Dev-Modus pythonw -m rigzdeck.desktop."""
    flag = "" if window else " --autostart"
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"{flag}'
    pyw = Path(sys.executable).with_name("pythonw.exe")
    exe = pyw if pyw.exists() else Path(sys.executable)
    return f'"{exe}" -m rigzdeck.desktop{flag}'


def autostart_mode() -> str:
    """``'off'`` | ``'tray'`` | ``'window'`` — abgeleitet aus dem Run-Eintrag (``--autostart`` = tray)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as k:
            val, _ = winreg.QueryValueEx(k, _AUTOSTART_NAME)
        return "tray" if "--autostart" in (val or "") else "window"
    except OSError:
        return "off"


def set_autostart_mode(mode: str) -> bool:
    """Autostart-Modus setzen: ``'off'`` (Eintrag löschen) · ``'tray'`` (still) · ``'window'`` (mit Fenster)."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if mode == "off":
                try:
                    winreg.DeleteValue(k, _AUTOSTART_NAME)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(k, _AUTOSTART_NAME, 0, winreg.REG_SZ,
                                  _autostart_command(window=(mode == "window")))
        return True
    except OSError:
        return False


def main() -> None:
    # Single-Instance: läuft schon eine Instanz, KEINE zweite starten (behebt „2 Tray-Icons nach
    # jedem Neustart" aus doppeltem Autostart ODER manuellem Doppelstart). Bei manuellem Start das
    # Fenster der laufenden Instanz holen, statt dass scheinbar „nichts passiert".
    if _already_running():
        if "--autostart" not in sys.argv:
            _open_window(f"http://127.0.0.1:{PORT}/")
        return

    import pystray

    srv = _Server()
    srv.start()
    local = f"http://127.0.0.1:{PORT}"
    lan = f"http://{_lan_ip()}:{PORT}"

    def open_editor(icon=None, item=None):
        _open_window(local + "/")

    def open_panel(icon=None, item=None):
        _open_window(local + "/panel")

    def copy_lan(icon=None, item=None):
        _copy_to_clipboard(lan + "/panel")

    def set_mode(mode):
        def _handler(icon=None, item=None):
            set_autostart_mode(mode)
        return _handler

    def quit_app(icon, item):
        srv.stop()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Editor öffnen", open_editor, default=True),
        pystray.MenuItem("Panel öffnen", open_panel),
        pystray.MenuItem(f"Tablet-URL kopieren  ({lan}/panel)", copy_lan),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Mit Windows starten", pystray.Menu(
            pystray.MenuItem("Aus", set_mode("off"),
                             checked=lambda item: autostart_mode() == "off", radio=True),
            pystray.MenuItem("Nur Tray (unsichtbar)", set_mode("tray"),
                             checked=lambda item: autostart_mode() == "tray", radio=True),
            pystray.MenuItem("Mit Fenster", set_mode("window"),
                             checked=lambda item: autostart_mode() == "window", radio=True),
        )),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", quit_app),
    )
    icon = pystray.Icon("RigzDeck", _tray_image(), "RigzDeck", menu)
    # Beim manuellen Start direkt den Editor zeigen; beim Autostart (--autostart) still in den Tray.
    if "--autostart" not in sys.argv:
        open_editor()
    icon.run()          # blockiert, bis „Beenden" gewählt wird


if __name__ == "__main__":
    main()
