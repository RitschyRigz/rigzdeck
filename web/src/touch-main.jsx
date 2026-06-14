import { render } from 'preact'
import { TouchDeck } from '@deckcore/TouchDeck.jsx'   // geteiltes Touch-Panel (deckcore)
import { PanelTheme } from './PanelTheme.jsx'
import { initTheme } from './theme.js'
import './base.css'

initTheme()   // Theme anwenden: lokales Override gewinnt, sonst Server-Theme (synced)

// RigzDeck-Panel: das geteilte Touch-Deck + ein kompakter Theme-Knopf fürs Gerät.
render(
  <div class="rd-panel"><PanelTheme /><TouchDeck /></div>,
  document.getElementById('app'),
)
