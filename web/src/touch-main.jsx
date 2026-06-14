import { render } from 'preact'
import { TouchDeck } from '@deckcore/TouchDeck.jsx'   // geteiltes Touch-Panel (deckcore)
import './base.css'

// RigzDeck-Panel: das geteilte Touch-Deck, vollflächig fürs Tablet.
render(
  <div class="rd-panel"><TouchDeck /></div>,
  document.getElementById('app'),
)
