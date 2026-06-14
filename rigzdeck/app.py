"""RigzDeck host — slim FastAPI app on the shared deckcore engine.

Serves the deck API (via deckcore's shared route layer), a multiplexed SSE feed for the
panels/editor, the built frontend (editor at ``/``, touch panel at ``/panel``), and uploaded
icons. No heavy backend — only the generic deck capabilities the core ships
(launch / http / flags / displayfusion / media / hotkey + the matching monitors).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from deckcore.service import DeckCoreService
from deckcore.api import build_streamdeck_router

from .bus import EventBus
from .defaults import RIGZDECK_DEFAULT_BUTTONS
from .discovery import Advertiser

# Pfade: im Dev relativ zum Repo; als gepackte .exe (PyInstaller, sys.frozen) read-only-
# Assets aus dem Bundle (sys._MEIPASS) und beschreibbarer State unter %APPDATA%\RigzDeck.
_PKG = Path(__file__).resolve().parent          # …/rigzdeck/rigzdeck
if getattr(sys, "frozen", False):
    _BUNDLE = Path(getattr(sys, "_MEIPASS", _PKG))   # entpacktes Bundle (read-only)
    _WEB_DIST = _BUNDLE / "web" / "dist"            # gebündeltes Frontend
    _DATA = Path(os.environ.get("APPDATA") or Path.home()) / "RigzDeck"   # beschreibbar
    _FILES_BASE = _DATA
else:
    _REPO = _PKG.parent                              # repo root
    _WEB_DIST = _REPO / "web" / "dist"              # built frontend (npm run build)
    _DATA = _PKG
    _FILES_BASE = _REPO
_RUNTIME = _DATA / "runtime"                          # streamdeck_buttons.json lives here
_FLAGS = _RUNTIME / "flags"                           # flag-capability dir
_STATIC = _DATA / "static"                            # uploaded/extracted icons (/static/sd_icons/user)

PORT = 7990


async def _one(topic, q):
    return topic, await q.get()


async def _sse_gen(request: Request, bus: EventBus, topics: list, initial: list):
    """Multiplexed SSE: one connection carries all requested topics. Yields the initial
    snapshot, then live payloads. (RigzDeck's deck needs only ~2 topics — one connection is
    plenty; the WebSocket transport is a planned next step to drop SSE entirely.)"""
    queues = [(t, bus.subscribe(t)) for t in topics]
    try:
        for t, payload in initial:
            yield {"event": t, "data": json.dumps(payload)}
        while True:
            if await request.is_disconnected():
                break
            tasks = [asyncio.create_task(_one(t, q)) for t, q in queues]
            done, pending = await asyncio.wait(tasks, timeout=10, return_when=asyncio.FIRST_COMPLETED)
            for p in pending:
                p.cancel()
            for d in done:
                try:
                    t, payload = d.result()
                    yield {"event": t, "data": json.dumps(payload)}
                except Exception:  # noqa: BLE001
                    pass
    finally:
        for t, q in queues:
            bus.unsubscribe(t, q)


def create_app() -> FastAPI:
    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _FLAGS.mkdir(parents=True, exist_ok=True)
    (_STATIC / "sd_icons" / "user").mkdir(parents=True, exist_ok=True)

    bus = EventBus()
    svc = DeckCoreService(
        bus,
        runtime_dir=_RUNTIME,
        flags_dir=_FLAGS,
        files_base=_FILES_BASE,
        self_base_url=f"http://127.0.0.1:{PORT}",
        default_buttons=RIGZDECK_DEFAULT_BUTTONS,
    )

    advertiser = Advertiser(PORT)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await svc.start()
        # zeroconfs Sync-API NICHT im laufenden Event-Loop aufrufen (sonst EventLoopBlocked
        # im Frozen-Build) -> Start/Stop in einem Worker-Thread (reiner Sync-Kontext).
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, advertiser.start)   # mDNS: App findet Host ohne IP
        try:
            yield
        finally:
            await loop.run_in_executor(None, advertiser.stop)
            await svc.stop()

    app = FastAPI(title="RigzDeck", version="0.1.0", lifespan=lifespan)
    app.state.bus = bus
    app.state.svc = svc

    def sse_response(request: Request, topics: list, initial: list):
        return EventSourceResponse(_sse_gen(request, bus, topics, initial), ping=15)

    # Shared deck API (registry/resolved/stream/press/buttons/decks + per-deck CRUD/displayfusion/icons)
    app.include_router(build_streamdeck_router(
        lambda request: svc, sse_response=sse_response, static_dir=_STATIC))

    @app.get("/api/events")
    async def events(request: Request):
        """Multiplexed SSE for the panels/editor (frontend useEventStream hits this)."""
        topics = [t for t in (request.query_params.get("topics") or "").split(",") if t]
        initial = []
        if "streamdeck:buttons" in topics:
            initial.append(("streamdeck:buttons", svc.resolved()))
        if "streamdeck:layout" in topics:
            initial.append(("streamdeck:layout", {"decks": svc.decks()}))
        return EventSourceResponse(_sse_gen(request, bus, topics, initial), ping=15)

    @app.get("/health")
    def health():
        return {"ok": True, "app": "RigzDeck", "version": "0.1.0",
                "buttons": len(svc.list_buttons()), "decks": len(svc.decks())}

    # Geteiltes Theme (Synced): der Editor schreibt es, Geräte ohne lokales Override folgen ihm.
    _theme_file = _RUNTIME / "theme.json"

    @app.get("/api/theme")
    def get_theme():
        try:
            if _theme_file.exists():
                return json.loads(_theme_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
        return {}

    @app.post("/api/theme")
    async def set_theme(request: Request):
        try:
            data = await request.json()
        except Exception:  # noqa: BLE001
            data = {}
        try:
            _theme_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True}

    # Uploaded icons (served at /static/sd_icons/user/…)
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
    # Built frontend assets (/assets/…) — only if the frontend has been built.
    if (_WEB_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(_WEB_DIST / "assets")), name="assets")

    @app.get("/")
    def index():
        f = _WEB_DIST / "index.html"
        if f.exists():
            return FileResponse(str(f))
        return PlainTextResponse(
            "RigzDeck-Frontend ist noch nicht gebaut.\nIm web/-Ordner:  npm install && npm run build",
            status_code=503)

    @app.get("/panel")
    def panel():
        f = _WEB_DIST / "touch.html"
        if f.exists():
            return FileResponse(str(f))
        return PlainTextResponse("RigzDeck-Panel-Build fehlt (web/: npm run build).", status_code=503)

    # Übrige gebaute Frontend-Dateien aus dem dist-Root (Favicon, Brand-Assets via web/public/, …).
    # ZULETZT gemountet → die expliziten Routen (/, /panel, /api, /assets, /static) matchen zuerst;
    # dieser Mount fängt nur den Rest (z.B. /monogram.ico, /rigzdeck-underlined.png).
    if _WEB_DIST.exists():
        app.mount("/", StaticFiles(directory=str(_WEB_DIST)), name="dist")

    return app


app = create_app()
