"""PyInstaller-Entry für die RigzDeck-.exe — startet den Tray-Launcher.

Eigene Datei auf Repo-Ebene, damit das ``rigzdeck``-Paket sauber als Paket importiert wird
(relative Imports in ``rigzdeck/desktop.py`` funktionieren so im Bundle).

Windowed-Builds (``console=False``) laufen ohne Konsole → ``sys.stdout``/``sys.stderr`` sind
``None``. Schreibt dann irgendeine Bibliothek (uvicorn/logging/click) dorthin, stirbt der
Prozess still mit Exit-Code 1. Darum VOR allem anderen die Ausgabe in ein Logfile umleiten —
das behebt den Absturz UND macht künftige Startfehler sichtbar (kein DEVNULL-Schlucken).
"""
import os
import sys
from pathlib import Path


def _log_path() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home()) / "RigzDeck" / "logs"
    base.mkdir(parents=True, exist_ok=True)
    return base / "rigzdeck.log"


def _redirect_streams() -> None:
    """Fehlende (None-)stdout/stderr eines Windowed-Builds auf ein Logfile umbiegen."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        f = open(_log_path(), "a", buffering=1, encoding="utf-8", errors="replace")
        if sys.stdout is None:
            sys.stdout = f
        if sys.stderr is None:
            sys.stderr = f
    except Exception:
        import io
        if sys.stdout is None:
            sys.stdout = io.StringIO()
        if sys.stderr is None:
            sys.stderr = io.StringIO()


if __name__ == "__main__":
    # Audio-Helfer-Subprozess: der winaudio-Client (deckcore) spawnt im eingefrorenen Build
    # `RigzDeck.exe --deckcore-winaudio-helper`. MUSS vor _redirect_streams laufen — der Helfer nutzt
    # stdout als JSON-IPC-Kanal (NICHT auf ein Logfile umbiegen!). So lebt das gesamte Core-Audio-COM
    # in einem eigenen Prozess → ein COM-Crash kann den Host nicht mitreißen.
    if "--deckcore-winaudio-helper" in sys.argv:
        from deckcore.winaudio_helper import main as _helper_main
        sys.exit(_helper_main())
    _redirect_streams()
    try:
        from rigzdeck.desktop import main
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise
