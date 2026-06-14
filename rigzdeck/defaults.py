"""Starter buttons for a fresh RigzDeck install — a small, universally-useful media row.

Only generic, machine-agnostic capabilities (media keys) so a brand-new install does something
immediately and shows what RigzDeck can do. The user adds/edits everything in the editor.
DeckCoreService seeds these into the pool and places them on the default deck (category = group).
"""

RIGZDECK_DEFAULT_BUTTONS: list[dict] = [
    {"id": "media_prev", "label": "Zurück", "group": "Media",
     "action": {"type": "media", "key": "prev"}, "monitor": {"type": "none"}, "states": [],
     "default": {"title": "Zurück", "icon": "⏮", "color": "#2f3037"}},
    {"id": "media_playpause", "label": "Play/Pause", "group": "Media",
     "action": {"type": "media", "key": "playpause"}, "monitor": {"type": "none"}, "states": [],
     "default": {"title": "Play / Pause", "icon": "⏯", "color": "#2f3037"}},
    {"id": "media_next", "label": "Weiter", "group": "Media",
     "action": {"type": "media", "key": "next"}, "monitor": {"type": "none"}, "states": [],
     "default": {"title": "Weiter", "icon": "⏭", "color": "#2f3037"}},
    {"id": "media_voldown", "label": "Leiser", "group": "Media",
     "action": {"type": "media", "key": "voldown"}, "monitor": {"type": "none"}, "states": [],
     "default": {"title": "Leiser", "icon": "🔉", "color": "#2f3037"}},
    {"id": "media_volup", "label": "Lauter", "group": "Media",
     "action": {"type": "media", "key": "volup"}, "monitor": {"type": "none"}, "states": [],
     "default": {"title": "Lauter", "icon": "🔊", "color": "#2f3037"}},
    {"id": "media_mute", "label": "Stumm", "group": "Media",
     "action": {"type": "media", "key": "mute"}, "monitor": {"type": "none"}, "states": [],
     "default": {"title": "Stumm", "icon": "🔇", "color": "#2f3037"}},
]
