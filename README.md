<p align="center">
  <img src="web/public/rigzdeck-lockup-underlined.png" alt="RigzDeck" width="540">
</p>

**Turn any tablet into a fully configurable stream deck.** A lightweight, standalone
stream-deck app — launch programs, switch DisplayFusion monitor profiles, control media,
fire hotkeys/macros, hit any HTTP endpoint, and more — all from a web panel on your
tablet(s) or the Elgato Stream Deck plugin. No heavy backend, no cloud.

RigzDeck is a slim host around the shared **[deckcore](https://github.com/RitschyRigz/deckcore)**
engine (included here as a git submodule) — a battle-tested deck editor, deck model, and
renderer wrapped in a minimal FastAPI app.

## Features (v0.1.0)

- **Decks** — independent view templates (own grid / categories / style), share a button pool.
- **WYSIWYG editor** — drag buttons into a live grid; per-button image + title overlay.
- **Generic capabilities** — `launch` (any .exe/.py/.lnk, native file picker + icon extraction),
  `displayfusion` (load monitor profiles), `media` (play/pause · ⏭⏮ · volume · mute),
  `hotkey` (send any key combo), `http`, `flag`; status monitors (poll/file/flag/displayfusion…).
- **Touch panel** over LAN for tablets + the Elgato Stream Deck plugin.

## Run (dev)

```bash
git clone --recurse-submodules https://github.com/RitschyRigz/rigzdeck.git
cd rigzdeck
pip install -r requirements.txt
( cd web && npm install && npm run build )
python -m rigzdeck            # → http://localhost:7990  (panel: /panel)
```

> Already cloned without submodules? `git submodule update --init --recursive`

## Package a Windows app (.exe)

```powershell
pip install -r requirements-build.txt
.\packaging\build.ps1        # builds the frontend, then bundles dist\RigzDeck\RigzDeck.exe
```

The `.exe` runs the server in the background and lives in the system tray — open the editor
or panel, copy the LAN URL for tablets, or quit. Optionally compile `packaging\RigzDeck.iss`
with [Inno Setup](https://jrsoftware.org/isinfo.php) for an installer (Start-menu shortcut,
optional autostart, uninstaller).

## Architecture

`rigzdeck/` (this host: FastAPI + event bus + static serving) → embeds `deckcore`
(`DeckCoreService` + `build_streamdeck_router`) → serves `web/` (Preact editor + touch panel,
which import the deck UI modules from `deckcore/web`).

## License

MIT — see [LICENSE](LICENSE).
