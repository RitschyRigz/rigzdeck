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


def main() -> None:
    import pystray

    srv = _Server()
    srv.start()
    local = f"http://127.0.0.1:{PORT}"
    lan = f"http://{_lan_ip()}:{PORT}"

    def open_editor(icon=None, item=None):
        webbrowser.open(local + "/")

    def open_panel(icon=None, item=None):
        webbrowser.open(local + "/panel")

    def copy_lan(icon=None, item=None):
        _copy_to_clipboard(lan + "/panel")

    def quit_app(icon, item):
        srv.stop()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Editor öffnen", open_editor, default=True),
        pystray.MenuItem("Panel öffnen", open_panel),
        pystray.MenuItem(f"Tablet-URL kopieren  ({lan}/panel)", copy_lan),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Beenden", quit_app),
    )
    icon = pystray.Icon("RigzDeck", _tray_image(), "RigzDeck", menu)
    open_editor()       # beim Start direkt den Editor zeigen
    icon.run()          # blockiert, bis „Beenden" gewählt wird


if __name__ == "__main__":
    main()
