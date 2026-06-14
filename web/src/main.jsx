import { render } from 'preact'
import { StreamDeck } from '@deckcore/StreamDeck.jsx'   // geteilter Deck-Editor (deckcore)
import './base.css'

// RigzDeck-Editor: der geteilte Deck-Editor in einer schlanken Hülle (nur der Editor).
render(
  <div class="rd-editor">
    <h1 class="rd-h">🎛 RigzDeck <span class="muted" style="font-size:13px;font-weight:400">— Deck-Editor</span></h1>
    <StreamDeck />
  </div>,
  document.getElementById('app'),
)
