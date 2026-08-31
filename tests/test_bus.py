"""RigzDeck EventBus-/SSE-Delivery-Regressionen — Delivery-Policy, Coalescing, Write-Timeout.

Belegt am echten Code des RigzDeck-Standalone-Hosts:
  * Coalescing (LATEST_VALUE) für die 3 verifizierten Deck-Snapshot-Topics → kein Rückstau.
  * FIFO-Policy für alles andere: droppt bei voller Queue + rate-limited Log + sub_id/client.
  * VOLLSTÄNDIGER PFAD: ein toter Client (blockierter Write) wird über den
    EventSourceResponse-send_timeout beendet → sse_starlette ruft aclose() auf dem echten
    rigzdeck.app._sse_gen → dessen finally räumt die Subscription GARANTIERT auf.
  * TEARDOWN: ein Abbruch des Generators mitten im asyncio.wait (Client-Disconnect/Cancel)
    lässt KEINE _one()-Reader-Tasks unreferenziert pending zurück („Task was destroyed but
    it is pending!"-Spam).
  * STARTUP-GUARD: port_bind_conflict erkennt einen belegten Port VOR dem uvicorn-Start.

Reine asyncio-Tests via asyncio.run() (kein pytest-asyncio nötig).
"""
from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Repo-Root (…/rigzdeck) in den Pfad → `rigzdeck` UND das `deckcore`-Submodul auflösbar.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rigzdeck.bus import EventBus, BusQueue, LATEST_VALUE_TOPICS, FIFO_MAXSIZE  # noqa: E402


class _WarnCounter(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.WARNING:
            self.messages.append(record.getMessage())


def _attach() -> _WarnCounter:
    h = _WarnCounter()
    logging.getLogger("rigzdeck.bus").addHandler(h)
    return h


class _FakeRequest:
    def __init__(self, host: str = "10.0.0.5") -> None:
        self.client = type("C", (), {"host": host})()

    async def is_disconnected(self) -> bool:
        return False


# ── LATEST_VALUE (coalescing) — payloads sind ROH (kein {topic,data,ts}-Wrapper) ─────────

def test_coalescing_topic_holds_only_latest_raw_payload():
    bus = EventBus()
    q = bus.subscribe("streamdeck:audio")
    assert q.latest_value is True and q.maxsize == 1
    for i in range(200):
        bus.publish("streamdeck:audio", {"vu": i})   # roher Snapshot-Payload
    assert q.qsize() == 1
    assert q.get_nowait() == {"vu": 199}              # der neueste, unverpackt
    assert q.dropped == 199


def test_all_three_deck_topics_are_latest_value_and_never_full():
    handler = _attach()
    try:
        bus = EventBus()
        assert LATEST_VALUE_TOPICS == frozenset(
            {"streamdeck:audio", "streamdeck:buttons", "streamdeck:layout"}
        )
        subs = {t: bus.subscribe(t) for t in LATEST_VALUE_TOPICS}
        for t in LATEST_VALUE_TOPICS:
            for i in range(1000):
                bus.publish(t, {"snapshot": i})
            assert subs[t].qsize() == 1
        assert [m for m in handler.messages if "queue voll" in m] == []
    finally:
        logging.getLogger("rigzdeck.bus").removeHandler(handler)


# ── FIFO-Policy (Default für nicht-Snapshot-Topics) ─────────────────────────────────────

def test_fifo_topic_drops_at_maxsize_and_logs_once():
    handler = _attach()
    try:
        bus = EventBus()
        q = bus.subscribe("some:fifo", client="10.0.0.5#7")   # nicht in LATEST_VALUE_TOPICS
        assert q.latest_value is False
        assert q.maxsize == FIFO_MAXSIZE == 512
        for i in range(FIFO_MAXSIZE + 40):                    # 512 rein, 40 gedroppt
            bus.publish("some:fifo", {"n": i})
        assert q.qsize() == 512
        assert q.dropped == 40
        assert q.get_nowait() == {"n": 0}                     # FIFO behält die ältesten
        full = [m for m in handler.messages if "queue voll" in m]
        assert len(full) == 1                                  # rate-limited: genau 1×
        assert f"sub={q.sub_id}" in full[0] and "client=10.0.0.5#7" in full[0]
    finally:
        logging.getLogger("rigzdeck.bus").removeHandler(handler)


def test_subscribe_returns_real_queue_and_unsubscribe_cleans_up():
    bus = EventBus()
    q = bus.subscribe("streamdeck:buttons", client="ip#1")
    assert isinstance(q, asyncio.Queue) and isinstance(q, BusQueue)
    assert q.sub_id >= 1 and q.client == "ip#1"
    bus.publish("streamdeck:buttons", {"buttons": {"a": 1}})
    assert q.get_nowait() == {"buttons": {"a": 1}}
    bus.unsubscribe("streamdeck:buttons", q)
    assert bus.subscriber_count("streamdeck:buttons") == 0


# ── Vollständiger Pfad — toter Client → send_timeout → Cleanup (echter _sse_gen) ─────────

async def _dead_client_scenario():
    import rigzdeck.app as ra
    from sse_starlette.sse import EventSourceResponse

    bus = EventBus()
    topic = "streamdeck:buttons"
    gen = ra._sse_gen(_FakeRequest(), bus, [topic], [])
    resp = EventSourceResponse(gen, ping=15, send_timeout=0.4)   # kurzer Timeout für den Test

    first_body = asyncio.Event()

    async def receive():
        await asyncio.Event().wait()
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.body" and message.get("body"):
            first_body.set()
            await asyncio.Event().wait()                        # toter Client: Write blockiert ewig

    scope = {
        "type": "http", "method": "GET", "path": "/", "raw_path": b"/",
        "headers": [], "query_string": b"", "scheme": "http",
        "client": ("10.0.0.5", 5555), "server": ("127.0.0.1", 7990),
        "asgi": {"version": "3.0", "spec_version": "2.3"},
    }

    async def _drive():
        try:
            await resp(scope, receive, send)
        except BaseException:
            pass

    drive = asyncio.create_task(_drive())
    try:
        for _ in range(200):
            if bus.subscriber_count(topic) == 1:
                break
            await asyncio.sleep(0.01)
        assert bus.subscriber_count(topic) == 1, "Subscription sollte nach subscribe existieren"

        bus.publish(topic, {"buttons": {"x": 1}})               # Generator yieldet → send blockiert
        await asyncio.wait_for(first_body.wait(), timeout=3.0)

        for _ in range(100):
            if bus.subscriber_count(topic) == 0:
                break
            await asyncio.sleep(0.05)
        assert bus.subscriber_count(topic) == 0, (
            "send_timeout MUSS die Subscription aufgeräumt haben (kein Zombie)"
        )
    finally:
        drive.cancel()
        try:
            await drive
        except BaseException:
            pass


def test_full_path_dead_client_is_cleaned_up_via_send_timeout():
    asyncio.run(_dead_client_scenario())


# ── Generator-Abbruch mitten im asyncio.wait → keine verwaisten Reader-Tasks ─────────────

async def _cancel_mid_wait_scenario():
    import rigzdeck.app as ra

    bus = EventBus()
    topic = "streamdeck:buttons"
    gen = ra._sse_gen(_FakeRequest(), bus, [topic], [])

    async def _drive():
        async for _ in gen:      # erster __anext__ → subscribe + rein ins asyncio.wait
            pass

    drive = asyncio.create_task(_drive())
    for _ in range(200):
        if bus.subscriber_count(topic) == 1:
            break
        await asyncio.sleep(0.01)
    assert bus.subscriber_count(topic) == 1, "Subscription sollte nach subscribe existieren"

    await asyncio.sleep(0.05)    # sicher IM asyncio.wait (idle, kein Publish)
    drive.cancel()               # der reale Pfad: uvicorn cancelt den Response-Task
    try:
        await drive
    except asyncio.CancelledError:
        pass

    assert bus.subscriber_count(topic) == 0, "finally muss die Subscription aufräumen"

    # Den Reader-Tasks ein paar Loop-Zyklen geben, ihre Cancellation zu verarbeiten — danach
    # darf KEIN Task mehr pending sein. (asyncio.wait lässt seine Kinder beim Abbruch
    # dokumentiert weiterlaufen; ohne Cancel im finally hängen sie unreferenziert an ihrer
    # Queue → GC → „Task was destroyed but it is pending!".)
    for _ in range(5):
        await asyncio.sleep(0)
    leftovers = [t for t in asyncio.all_tasks()
                 if t is not asyncio.current_task() and not t.done()]
    assert leftovers == [], f"verwaiste pending Reader-Tasks: {leftovers}"


def test_generator_cancel_mid_wait_leaves_no_pending_reader_tasks():
    asyncio.run(_cancel_mid_wait_scenario())


# ── Startup-Guard: Port-Bind-Konflikt erkennen, BEVOR uvicorn die Lifespan hochfährt ─────

def test_port_bind_conflict_detects_taken_and_free_port():
    import socket

    import rigzdeck.app as ra

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", 0))
        port = s.getsockname()[1]
        assert ra.port_bind_conflict(port) is True    # belegt → Konflikt erkannt
    finally:
        s.close()
    assert ra.port_bind_conflict(port) is False       # wieder frei → kein Konflikt
