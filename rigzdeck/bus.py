"""Minimal in-process event bus for RigzDeck.

DeckCoreService publishes resolved button visuals (topic ``streamdeck:buttons``) and deck-config
(``streamdeck:layout``) here; the SSE endpoints subscribe and stream them to panels/plugin.

Contract (matches what DeckCoreService expects):
  • ``publish(topic, payload)`` — fan out a payload to every subscriber of that topic.
  • ``subscribe(topic) -> asyncio.Queue`` — each ``await q.get()`` yields the next payload for
    that topic.
  • ``unsubscribe(topic, q)`` — drop a subscriber.
"""
from __future__ import annotations

import asyncio


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, set] = {}

    def publish(self, topic, payload) -> None:
        for q in list(self._subs.get(topic, ())):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass  # slow consumer — drop (deck visuals are last-write-wins anyway)

    def subscribe(self, topic):
        q: asyncio.Queue = asyncio.Queue(maxsize=512)
        self._subs.setdefault(str(topic), set()).add(q)
        return q

    def unsubscribe(self, topic, q) -> None:
        s = self._subs.get(str(topic))
        if s:
            s.discard(q)
            if not s:
                self._subs.pop(str(topic), None)
