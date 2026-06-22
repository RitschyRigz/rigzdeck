"""RigzDeck — a lightweight standalone Stream-Deck app on the shared deckcore engine.

Turns any tablet (or the Elgato plugin) into a fully configurable stream deck, without any
heavy backend machinery. The deck logic lives in `deckcore`; this package is just the slim
host (FastAPI server + event bus + static serving).
"""
__version__ = "0.12.0"
