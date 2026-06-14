"""mDNS-Anmeldung des RigzDeck-Hosts im LAN (zero-config).

Damit findet die Android-App den Host automatisch — ohne dass jemand IP/Port eintippt.
Angemeldet wird der Dienst `_rigzdeck._tcp.local.` auf dem gegebenen Port. Faellt still
aus, wenn `zeroconf` fehlt (dann konfiguriert man die App eben manuell).
"""
from __future__ import annotations

import socket
from contextlib import suppress


def lan_ip() -> str:
    """Beste lokale LAN-IP (fuer die mDNS-Adresse); Fallback 127.0.0.1."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        with suppress(Exception):
            s.close()


class Advertiser:
    """Meldet den RigzDeck-Host als `_rigzdeck._tcp.local.` im Netzwerk an."""

    def __init__(self, port: int):
        self.port = port
        self._zc = None
        self._info = None

    def start(self) -> None:
        try:
            from zeroconf import ServiceInfo, Zeroconf
        except Exception:
            import traceback
            print("[discovery] zeroconf-Import fehlgeschlagen:", flush=True)
            traceback.print_exc()
            return  # zeroconf fehlt -> App muss manuell konfiguriert werden
        try:
            ip = lan_ip()
            host = (socket.gethostname().split(".")[0] or "host").replace(" ", "-")
            self._zc = Zeroconf()
            self._info = ServiceInfo(
                "_rigzdeck._tcp.local.",
                f"RigzDeck-{host}._rigzdeck._tcp.local.",
                addresses=[socket.inet_aton(ip)],
                port=self.port,
                properties={"path": "/panel", "app": "RigzDeck"},
                server=f"rigzdeck-{host}.local.",
            )
            self._zc.register_service(self._info)
            print(f"[discovery] mDNS angemeldet: _rigzdeck._tcp @ {ip}:{self.port}", flush=True)
        except Exception:
            import traceback
            print("[discovery] mDNS-Anmeldung fehlgeschlagen:", flush=True)
            traceback.print_exc()
            self.stop()

    def stop(self) -> None:
        with suppress(Exception):
            if self._zc and self._info:
                self._zc.unregister_service(self._info)
        with suppress(Exception):
            if self._zc:
                self._zc.close()
        self._zc = None
        self._info = None
