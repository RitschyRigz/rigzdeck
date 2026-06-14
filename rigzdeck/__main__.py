"""Run RigzDeck:  python -m rigzdeck  (serves on 0.0.0.0:7990 so LAN tablets can connect)."""
import uvicorn

from .app import PORT

if __name__ == "__main__":
    uvicorn.run("rigzdeck.app:app", host="0.0.0.0", port=PORT, log_level="info")
