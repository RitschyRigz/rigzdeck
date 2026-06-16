"""Audio-Switch-Buttons fuer ein deckcore-Deck anlegen (RigzDeck ODER Cockpit).

Legt an:
  * einen Kopplungs-Toggle  (Wave Link folgt dem Windows-Standardgeraet — opt-in, leuchtet wenn aktiv)
  * pro Eintrag in DEVICES einen "Windows-Standard setzen"-Button (gruen = aktuell aktiv)

Die Geraete werden per NAMENS-TEILSTRING aufgeloest (robust gegen wechselnde Endpoint-IDs /
"-2"-Suffixe beim Neu-Einstecken). Trage unten deine Geraete ein und starte das Skript einmal
auf dem Rechner, dessen RigzDeck/Cockpit du bestuecken willst (oder gegen dessen URL im LAN).

  python tools/setup_audio_switch.py

Voraussetzung: das Ziel (RigzDeck :7990 / Cockpit :7883) laeuft und nutzt ein deckcore mit
winaudio-Support (Capability 'winaudio' + Monitor 'winaudio_default').
"""
import json
import sys
import urllib.request

# ─────────────────────────── KONFIG ───────────────────────────
BASE = "http://127.0.0.1:7990"      # RigzDeck = :7990, Cockpit = :7883
DECK_LABEL = "Audio"                # Ziel-Deck (wird angelegt, falls nicht vorhanden)
COUPLING = True                     # Kopplungs-Toggle anlegen? (braucht Wave Link am Geraet)

# Pro Eintrag ein Button. "name" = Teilstring des Windows-Geraetenamens (case-insensitive).
# Beispiele (anpassen!):  "ROG CETRA"  ·  "Realtek USB"  ·  "Pebble"  ·  "Speakers"
DEVICES = [
    {"title": "Kopfhörer",    "icon": "🎧", "name": "ROG CETRA"},
    {"title": "Lautsprecher", "icon": "🔊", "name": "Realtek USB"},
]
# ───────────────────────────────────────────────────────────────


def call(path, body=None, method=None):
    data = json.dumps(body).encode() if body is not None else None
    m = method or ("POST" if body is not None else "GET")
    req = urllib.request.Request(BASE + path, data=data, method=m,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read().decode())


def slug(s):
    return "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")


def main():
    try:
        reg = call("/api/streamdeck/registry")
    except Exception as e:
        print(f"Ziel {BASE} nicht erreichbar: {e}")
        sys.exit(1)

    deck = next((d for d in reg.get("decks", []) if d.get("label", "").lower() == DECK_LABEL.lower()), None)
    deck_id = deck["id"] if deck else call("/api/streamdeck/deck/add",
                                           {"label": DECK_LABEL, "icon": "🔊"}).get("id")
    print(f"Deck: {DECK_LABEL} ({deck_id})")

    def place(bid):
        call(f"/api/streamdeck/deck/{deck_id}/item", {"button": bid})

    if COUPLING:
        call("/api/streamdeck/buttons", {
            "id": "wl_couple_toggle", "label": "Kopplung Win-WL",
            "action": {"type": "flag_toggle", "flag": "wavelink_follow_default.flag"},
            "monitor": {"type": "flag", "flag": "wavelink_follow_default.flag"},
            "states": [{"when": {"op": "truthy"}, "icon": "🔗", "title": "Kopplung AN", "color": "#1f9d55"}],
            "default": {"icon": "🔓", "title": "Kopplung AUS", "color": "#2a2a2a"}})
        place("wl_couple_toggle")
        print("  + Kopplungs-Toggle")

    for d in DEVICES:
        bid = "win_out_" + slug(d["name"])
        call("/api/streamdeck/buttons", {
            "id": bid, "label": d["title"],
            "action": {"type": "winaudio", "wa_action": "set_default", "device_name": d["name"]},
            "monitor": {"type": "winaudio_default", "device_name": d["name"]},
            "states": [{"when": {"op": "truthy"}, "icon": d["icon"], "title": d["title"], "color": "#1f9d55"}],
            "default": {"icon": d["icon"], "title": d["title"], "color": "#2a2a2a"}})
        place(bid)
        print(f"  + {d['title']}  (matcht: {d['name']})")

    print("Fertig. Deck-Tab '%s' im Panel pruefen." % DECK_LABEL)


if __name__ == "__main__":
    main()
