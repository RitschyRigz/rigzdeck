"""In-process event bus for RigzDeck with a per-topic delivery policy.

DeckCoreService publishes deck visuals (``streamdeck:buttons`` / ``streamdeck:layout``) and
VU telemetry (``streamdeck:audio``) here; the SSE endpoint (``app._sse_gen``) AND the
service's own ``sse_field`` loop subscribe and read via ``await q.get()``.

DELIVERY POLICY per topic
-------------------------
* **FIFO (default):** every payload matters. A full/slow subscriber's NEW payloads are
  dropped (rate-limited log), others keep flowing (a hung panel must not stall the rest).
* **LATEST_VALUE (coalescing):** the producer pushes a COMPLETE snapshot each time and old
  values are worthless. The queue holds only the NEWEST payload → no backlog, never
  ``QueueFull``. All three deck topics are last-write-wins (verified in
  ``deckcore/service.py``: ``streamdeck:buttons``={buttons: _resolved} ·
  ``streamdeck:layout``={decks: …} · ``streamdeck:audio``=frame). Only add a topic to
  ``LATEST_VALUE_TOPICS`` if BOTH producer and consumer are unambiguously last-write-wins.

DEAD SUBSCRIBERS
----------------
The bus never proactively removes anyone (it does not know the transport). A dead/half-open
SSE subscriber (a blocked write) is torn down SERVER-SIDE via the ``send_timeout`` on the
``EventSourceResponse`` (see app.py): sse_starlette aborts the stuck send and calls
``aclose()`` on the generator → its ``finally`` calls ``unsubscribe`` here. The bus only
makes an overflowing FIFO subscriber VISIBLE (sub_id + client + rate-limited log) and keeps
LATEST_VALUE topics harmless by coalescing from the start.

Contract (unchanged for consumers): ``subscribe(topic[, client]) -> asyncio.Queue`` ·
``await q.get()`` yields the next payload · ``unsubscribe(topic, q)`` drops it.
"""
from __future__ import annotations

import asyncio
import itertools
import logging

log = logging.getLogger("rigzdeck.bus")

# Latest-Value (coalescing) topics — producer pushes a complete snapshot, old values
# worthless, consumer replaces the whole state (TouchDeck.jsx: buttons→pushVis, audio→VU,
# layout→deck list). Verified against deckcore/service.py's publish sites.
LATEST_VALUE_TOPICS = frozenset({
    "streamdeck:audio",
    "streamdeck:buttons",
    "streamdeck:layout",
})

FIFO_MAXSIZE = 512   # generous FIFO backlog (unchanged default for any non-snapshot topic)


class BusQueue(asyncio.Queue):
    """A subscriber queue with identity + delivery policy.

    Stays a real ``asyncio.Queue`` (consumers keep using ``await q.get()``). Adds
    ``sub_id``/``topic``/``client`` for diagnostics, ``latest_value`` (coalescing),
    ``dropped`` (count of discarded payloads) and rate-limited QueueFull logging.
    """

    def __init__(self, *, sub_id: int, topic: str, client, latest_value: bool) -> None:
        super().__init__(maxsize=1 if latest_value else FIFO_MAXSIZE)
        self.sub_id = sub_id
        self.topic = topic
        self.client = client
        self.latest_value = latest_value
        self.dropped = 0
        self._full_logged = False

    def offer(self, payload) -> None:
        """Deliver one payload (called from the sync ``publish``)."""
        if self.latest_value:
            # Coalesce: always keep only the newest snapshot.
            if self.full():
                try:
                    self.get_nowait()
                    self.dropped += 1
                except asyncio.QueueEmpty:
                    pass
            try:
                self.put_nowait(payload)
            except asyncio.QueueFull:
                pass  # unreachable after get_nowait; defensive
            return

        try:
            self.put_nowait(payload)
            if self._full_logged:
                self._full_logged = False   # recovered → the next overflow logs again
        except asyncio.QueueFull:
            self.dropped += 1
            if not self._full_logged:
                self._full_logged = True
                log.warning(
                    "EventBus: queue voll sub=%s topic=%s client=%s — dropping payloads "
                    "(further messages suppressed until it recovers)",
                    self.sub_id, self.topic, self.client or "?",
                )


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, set] = {}
        self._sub_ids = itertools.count(1)

    def publish(self, topic, payload) -> None:
        for q in list(self._subs.get(str(topic), ())):
            q.offer(payload)

    def subscribe(self, topic, client=None):
        sub_id = next(self._sub_ids)
        q = BusQueue(
            sub_id=sub_id, topic=str(topic), client=client,
            latest_value=str(topic) in LATEST_VALUE_TOPICS,
        )
        self._subs.setdefault(str(topic), set()).add(q)
        log.debug("EventBus: subscribe sub=%s topic=%s client=%s policy=%s",
                  sub_id, topic, client or "?",
                  "latest_value" if q.latest_value else "fifo")
        return q

    def unsubscribe(self, topic, q) -> None:
        s = self._subs.get(str(topic))
        if s:
            s.discard(q)
            if not s:
                self._subs.pop(str(topic), None)
        log.debug("EventBus: unsubscribe sub=%s topic=%s client=%s dropped=%d",
                  getattr(q, "sub_id", "?"), topic,
                  getattr(q, "client", None) or "?", getattr(q, "dropped", 0))

    def subscriber_count(self, topic) -> int:
        return len(self._subs.get(str(topic), ()))
