"""Run RigzDeck:  python -m rigzdeck  (serves on 0.0.0.0:7990 so LAN tablets can connect)."""
import sys

import uvicorn

from .app import port_bind_conflict, PORT

if __name__ == "__main__":
    # Startup-Guard vor uvicorn: uvicorn fährt erst die komplette Lifespan hoch (Service,
    # mDNS, Verbindungen) und bindet DANACH — ein belegter Port endet sonst als Traceback +
    # mDNS-Spam statt als eine klare Zeile.
    if port_bind_conflict(PORT):
        sys.exit(f"RigzDeck: Port {PORT} ist bereits belegt — läuft schon eine Instanz? Abbruch.")
    uvicorn.run("rigzdeck.app:app", host="0.0.0.0", port=PORT, log_level="info")
