import { render } from 'preact'
import { useState } from 'preact/hooks'
import { StreamDeck } from '@deckcore/StreamDeck.jsx'   // geteilter Deck-Editor (deckcore)
import { Theme } from './Theme.jsx'
import { Obs } from './Obs.jsx'
import { VersionBadge } from './VersionBadge.jsx'
import { OfflineScreen } from './OfflineScreen.jsx'
import { initTheme } from './theme.js'
import './base.css'

initTheme()   // gespeichertes Theme (pro Gerät) sofort anwenden

// RigzDeck-Editor: geteilter Deck-Editor + Theme-Tab in einer schlanken Hülle.
function App() {
  const [tab, setTab] = useState('deck')
  return (
    <div class="rd-editor">
      <div class="rd-head">
        <h1 class="rd-brand">
          <img class="rd-logo" src="/monogram-256.png" alt="" aria-hidden="true" />
          <img class="rd-wordmark" src="/rigzdeck-underlined.png" alt="RigzDeck" />
        </h1>
        <div class="rd-tabs">
          <button class={'rd-tab' + (tab === 'deck' ? ' on' : '')} onClick={() => setTab('deck')}>Deck</button>
          <button class={'rd-tab' + (tab === 'theme' ? ' on' : '')} onClick={() => setTab('theme')}>Theme</button>
          <button class={'rd-tab' + (tab === 'obs' ? ' on' : '')} onClick={() => setTab('obs')}>OBS</button>
        </div>
      </div>
      {tab === 'deck' ? <StreamDeck /> : tab === 'theme' ? <Theme /> : <Obs />}
      <VersionBadge />
      <OfflineScreen />
    </div>
  )
}

render(<App />, document.getElementById('app'))
