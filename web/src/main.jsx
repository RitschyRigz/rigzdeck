import { render } from 'preact'
import { useState } from 'preact/hooks'
import { StreamDeck } from '@deckcore/StreamDeck.jsx'   // geteilter Deck-Editor (deckcore)
import { Theme } from './Theme.jsx'
import { initTheme } from './theme.js'
import './base.css'

initTheme()   // gespeichertes Theme (pro Gerät) sofort anwenden

// RigzDeck-Editor: geteilter Deck-Editor + Theme-Tab in einer schlanken Hülle.
function App() {
  const [tab, setTab] = useState('deck')
  return (
    <div class="rd-editor">
      <div class="rd-head">
        <h1 class="rd-h">🎛 RigzDeck <span class="muted" style="font-size:13px;font-weight:400">— {tab === 'deck' ? 'Deck-Editor' : 'Theme'}</span></h1>
        <div class="rd-tabs">
          <button class={'rd-tab' + (tab === 'deck' ? ' on' : '')} onClick={() => setTab('deck')}>Deck</button>
          <button class={'rd-tab' + (tab === 'theme' ? ' on' : '')} onClick={() => setTab('theme')}>Theme</button>
        </div>
      </div>
      {tab === 'deck' ? <StreamDeck /> : <Theme />}
    </div>
  )
}

render(<App />, document.getElementById('app'))
