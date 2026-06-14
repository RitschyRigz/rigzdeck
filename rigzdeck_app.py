"""PyInstaller-Entry für die RigzDeck-.exe — startet den Tray-Launcher.

Eigene Datei auf Repo-Ebene, damit das ``rigzdeck``-Paket sauber als Paket importiert wird
(relative Imports in ``rigzdeck/desktop.py`` funktionieren so im Bundle).
"""
from rigzdeck.desktop import main

if __name__ == "__main__":
    main()
