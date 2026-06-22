import { useState, useEffect } from 'preact/hooks'
import {
  CORE_VARS, SEMANTIC_VARS, PRESETS, DEFAULT_ID,
  loadLocal, saveLocal, resolveVars, applyVars, contrastRatio,
  fetchServerTheme, pushServerThemeDebounced,
} from './theme.js'
import { Glyph } from '@deckcore/icons.jsx'
import { TILE_SKINS, PRESS_MODES, THEME_COLORS, applyDeckLook, LOOK_DEFAULT } from '@deckcore/deckstyle.js'

// 🎨 Theme-Tab — RigzDeck personalisieren. Theme (Presets/eigene Farben) + globaler Kachel-Stil +
// Druck-Bestätigung + Ordner-Rahmen + Speichern/Teilen. Der Editor ist MASTER: Änderungen wirken sofort
// live UND werden als GETEILTES Theme auf den Server geschrieben → alle Geräte ohne eigenes Override
// folgen automatisch (z.B. das Tablet-Panel). deckcore bleibt unberührt (nur CSS-Variablen + body-data).

// Vorschau-Kachel im echten Deck-Look (deck.css .t-key/.t-flat/.s-*). Tippen → Druck-Animation (zeigt den
// gewählten Druck-Modus, weil applyLook body[data-press] gesetzt hat).
function PrevKey({ skin, color, title, label, children, folder }) {
  const [p, setP] = useState(false)
  return (
    <button class={'t-key t-flat cqsize s-' + (skin || 'brackets') + (folder ? ' is-folder' : '') + (p ? ' pressed' : '')}
            style={`--acc:${color || 'var(--accent)'}`}
            onClick={() => { setP(true); setTimeout(() => setP(false), 280) }}>
      <span class="t-key-icon">{children}</span>
      {title && <span class="t-key-title">{title}</span>}
      {label && <span class="t-key-label">{label}</span>}
      {folder && <span class="t-folder-badge">⋯</span>}
    </button>
  )
}

// Theme-Farb-Swatches (Akzent/Live/…) + „eigene Farbe" — für Druck-/Ordnerfarbe.
function ColorPick({ value, onPick }) {
  return (
    <span style="display:inline-flex;align-items:center;gap:5px;vertical-align:middle">
      {Object.keys(THEME_COLORS).map((k) => (
        <button key={k} type="button" title={'Theme: ' + THEME_COLORS[k]} onClick={() => onPick(k)}
                style={`width:16px;height:16px;border-radius:5px;cursor:pointer;background:var(--${k});border:1px solid rgba(255,255,255,.28)` + (value === k ? ';outline:2px solid var(--fg);outline-offset:1px' : '')} />
      ))}
      <input type="color" value={(value && value[0] === '#') ? value : '#888888'} title="Eigene Farbe"
             onInput={(e) => onPick(e.currentTarget.value)}
             style="width:30px;height:26px;border:1px solid var(--line);border-radius:6px;background:none;cursor:pointer;padding:0" />
    </span>
  )
}

export function Theme() {
  const initCustoms = loadLocal().customs
  const [st, setSt] = useState({ activeId: DEFAULT_ID, adhoc: null, customs: initCustoms })
  const [vars, setVars] = useState(() => resolveVars({ activeId: DEFAULT_ID, adhoc: null }, initCustoms))
  const [look, setLook] = useState(LOOK_DEFAULT)
  const [adv, setAdv] = useState(false)
  const [name, setName] = useState('')
  const [msg, setMsg] = useState('')
  const [decks, setDecks] = useState([])   // für die Deck-Theme-Overrides (nur Top-Level, keine Ordner)

  // Registry liefert die Decks (für Deck-Themes) UND den globalen Look (Kachel-Stil/Druck/Ordner) — der lebt
  // jetzt generisch in deckcore (nicht mehr im Hüllen-Theme). Hier nur spiegeln + live anwenden.
  const refreshDecks = () => fetch('/api/streamdeck/registry').then((r) => r.json())
    .then((d) => {
      setDecks((d.decks || []).filter((x) => !x.folder && !x.auto))
      const nl = { ...LOOK_DEFAULT, ...(d.look || {}) }; setLook(nl); applyDeckLook(nl)
    }).catch(() => {})
  useEffect(() => { refreshDecks() }, [])

  // Beim Öffnen das aktuell geteilte (Server-)Theme + Look laden, damit der Editor den echten Stand zeigt.
  useEffect(() => {
    let alive = true
    fetchServerTheme().then((srv) => {
      if (!alive || !srv) return
      if (srv.vars) {
        const nv = { ...PRESETS[DEFAULT_ID].vars, ...srv.vars }
        setSt((s) => ({ ...s, activeId: srv.activeId || '__adhoc', adhoc: srv.adhoc || null }))
        setVars(nv); applyVars(nv)
      }
    })
    return () => { alive = false }
  }, [])

  // Farb-Theme → Server (debounced, theme.json). Der globale LOOK lebt getrennt in deckcore (siehe editLook).
  function push(st2, vars2) {
    pushServerThemeDebounced({ activeId: st2.activeId, adhoc: st2.adhoc, vars: vars2 })
  }
  function commit(nextSt, nextVars) {
    setSt(nextSt); setVars(nextVars); applyVars(nextVars)
    saveLocal({ override: loadLocal().override, customs: nextSt.customs })
    push(nextSt, nextVars)
  }
  // Globaler Look → generische deckcore-Einstellung (/api/streamdeck/look), NICHT mehr ins Hüllen-Theme.
  function editLook(patch) {
    const nl = { ...look, ...patch }
    setLook(nl); applyDeckLook(nl)
    fetch('/api/streamdeck/look', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) }).catch(() => {})
  }
  function applyPreset(id) {
    setMsg(''); commit({ ...st, activeId: id, adhoc: null }, { ...PRESETS[DEFAULT_ID].vars, ...PRESETS[id].vars })
  }
  function editVar(key, val) {
    const nv = { ...vars, [key]: val }
    commit({ ...st, activeId: '__adhoc', adhoc: { ...nv } }, nv)
  }
  function applyCustom(nm) {
    setMsg(''); commit({ ...st, activeId: '__custom:' + nm, adhoc: null }, { ...PRESETS[DEFAULT_ID].vars, ...st.customs[nm] })
  }
  function saveCustom() {
    const nm = name.trim()
    if (!nm) { setMsg('Bitte einen Namen vergeben.'); return }
    const customs = { ...st.customs, [nm]: { ...vars } }
    commit({ ...st, customs, activeId: '__custom:' + nm }, vars)
    setName(''); setMsg('Gespeichert: ' + nm)
  }
  function deleteCustom(nm) {
    const customs = { ...st.customs }; delete customs[nm]
    if (st.activeId === '__custom:' + nm) {
      commit({ ...st, customs, activeId: DEFAULT_ID }, { ...PRESETS[DEFAULT_ID].vars })
    } else {
      const nextSt = { ...st, customs }; setSt(nextSt)
      saveLocal({ override: loadLocal().override, customs })
    }
  }
  function reset() { applyPreset(DEFAULT_ID) }

  // ── Deck-Theme-Override: einem Deck ein eigenes Theme geben (oder '' = globalem Theme folgen) ──
  function deckThemeValue(d) {   // aktuelle Auswahl als Dropdown-Wert (Preset-id / __custom:name / '')
    if (!d.theme || !d.theme.name) return ''
    const pid = Object.keys(PRESETS).find((id) => PRESETS[id].name === d.theme.name)
    if (pid) return pid
    if ((st.customs || {})[d.theme.name]) return '__custom:' + d.theme.name
    return ''
  }
  function setDeckTheme(deckId, sel) {
    let payload = null
    if (PRESETS[sel]) payload = { name: PRESETS[sel].name, vars: { ...PRESETS[DEFAULT_ID].vars, ...PRESETS[sel].vars } }
    else if (sel.indexOf('__custom:') === 0) {
      const nm = sel.slice(9)
      if ((st.customs || {})[nm]) payload = { name: nm, vars: { ...PRESETS[DEFAULT_ID].vars, ...st.customs[nm] } }
    }
    setDecks((ds) => ds.map((d) => d.id === deckId ? { ...d, theme: payload } : d))   // optimistisch
    fetch('/api/streamdeck/deck/' + encodeURIComponent(deckId) + '/theme', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: payload }),
    }).catch(() => {})
  }

  function exportTheme() {
    const data = JSON.stringify({ name: activeName(), vars, look }, null, 2)
    try {
      const blob = new Blob([data], { type: 'application/json' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = 'rigzdeck-theme.json'
      a.click(); URL.revokeObjectURL(a.href)
    } catch (e) { /* Download evtl. blockiert */ }
    try { navigator.clipboard.writeText(data) } catch (e) { /* kein Clipboard */ }
    setMsg('Exportiert (Datei + Zwischenablage).')
  }
  function importTheme(e) {
    const f = e.target.files && e.target.files[0]
    if (!f) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const obj = JSON.parse(reader.result)
        const v = obj && obj.vars ? obj.vars : obj
        const nv = { ...PRESETS[DEFAULT_ID].vars, ...v }
        if (obj && obj.look) { const nl = { ...LOOK_DEFAULT, ...obj.look }; setLook(nl); applyDeckLook(nl)
          fetch('/api/streamdeck/look', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(obj.look) }).catch(() => {}) }
        commit({ ...st, activeId: '__adhoc', adhoc: { ...nv } }, nv)
        setMsg('Importiert' + (obj && obj.name ? ': ' + obj.name : '') + ' — zum Behalten unten benennen + speichern.')
      } catch (err) { setMsg('Import fehlgeschlagen (kein gültiges Theme-JSON).') }
    }
    reader.readAsText(f); e.target.value = ''
  }
  function activeName() {
    const id = st.activeId
    if (PRESETS[id]) return PRESETS[id].name
    if (id && id.indexOf('__custom:') === 0) return id.slice('__custom:'.length)
    return 'Eigenes (ungespeichert)'
  }

  const cr = contrastRatio(vars['--bg'], vars['--fg'])
  const lowContrast = cr != null && cr < 4.5
  const customNames = Object.keys(st.customs || {})

  const colorRow = (v) => (
    <div class="th-row" key={v.key}>
      <label>{v.label}</label>
      <input type="color" value={vars[v.key]} onInput={(e) => editVar(v.key, e.currentTarget.value)} />
      <input type="text" value={vars[v.key]} spellcheck={false}
             onChange={(e) => editVar(v.key, e.currentTarget.value)} />
    </div>
  )
  const fieldStyle = 'display:flex;flex-direction:column;gap:5px;font-size:13px;font-weight:600;color:var(--muted)'
  const selStyle = 'background:var(--bg3);color:var(--fg);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font:inherit;min-width:170px'

  return (
    <div class="th">
      <p class="hint">Personalisiere RigzDeck — wirkt sofort und gilt als <b>geteiltes Theme für alle Geräte</b>.
        Ein Tablet kann im Panel (🎨) lokal abweichen, z.B. OLED-Schwarz. Einzelne Decks können später ein eigenes Theme bekommen.</p>

      {/* ── Look & Verhalten: Theme · Kachel-Stil · Druck · Ordner + Live-Vorschau ── */}
      <h2 class="th-sec">🎛 Look &amp; Verhalten</h2>
      <div style="display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start">
        <div style="display:flex;flex-direction:column;gap:14px;min-width:240px">
          <label style={fieldStyle}>Theme
            <select style={selStyle} value={st.activeId}
                    onChange={(e) => { const v = e.currentTarget.value; v.indexOf('__custom:') === 0 ? applyCustom(v.slice(9)) : applyPreset(v) }}>
              {Object.keys(PRESETS).map((id) => <option value={id}>{PRESETS[id].name}</option>)}
              {st.activeId === '__adhoc' && <option value="__adhoc">Eigene Farben</option>}
              {customNames.length > 0 && <optgroup label="Eigene Themes">{customNames.map((nm) => <option value={'__custom:' + nm}>{nm}</option>)}</optgroup>}
            </select>
          </label>
          <label style={fieldStyle}>Kachel-Stil (global)
            <select style={selStyle} value={look.tile} onChange={(e) => editLook({ tile: e.currentTarget.value })}>
              {TILE_SKINS.map(([v, l]) => <option value={v}>{l}</option>)}
            </select>
          </label>
          <div style={fieldStyle}>Druck-Bestätigung
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <select style={selStyle} value={look.press} onChange={(e) => editLook({ press: e.currentTarget.value })}>
                {PRESS_MODES.map(([v, l]) => <option value={v}>{l}</option>)}
              </select>
              <ColorPick value={look.pressColor} onPick={(c) => editLook({ pressColor: c })} />
            </div>
          </div>
          <div style={fieldStyle}>Ordner-Rahmen
            <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
              <label style="display:inline-flex;align-items:center;gap:6px;color:var(--fg);font-weight:500">
                <input type="checkbox" checked={look.folder !== false} onChange={(e) => editLook({ folder: e.currentTarget.checked })} /> anzeigen
              </label>
              {look.folder !== false && <ColorPick value={look.folderColor} onPick={(c) => editLook({ folderColor: c })} />}
            </div>
          </div>
        </div>
        <div style="flex:1;min-width:260px">
          <div style="display:grid;grid-template-columns:repeat(auto-fill,92px);gap:12px;--sd-size:92px;--sd-font:.92">
            <PrevKey skin={look.tile} title="Play" label="Media"><Glyph name="play" /></PrevKey>
            <PrevKey skin={look.tile} color="var(--accent2)" title="OBS" label="Szene"><Glyph name="video" /></PrevKey>
            <PrevKey skin={look.tile} color="var(--live)" title="Live" label="Stream">🔴</PrevKey>
            <PrevKey skin={look.tile} folder title="Ordner" label="öffnet">📁</PrevKey>
          </div>
          <p class="th-prev-cap muted" style="margin-top:10px">Live-Vorschau — <b>tippe eine Kachel</b> für die Druck-Animation.
            Stil, Theme &amp; Ordner-Rahmen oben ändern → alles passt sich sofort an.</p>
        </div>
      </div>

      {/* ── Deck-Themes: einzelnen Decks ein eigenes Theme geben (Identität, z.B. rot=Dual / blau=Solo) ── */}
      <h2 class="th-sec">🎯 Deck-Themes <span class="muted" style="font-size:13px;font-weight:400">— einzelne Decks einfärben</span></h2>
      <p class="hint">Gib einem Deck ein eigenes Theme — beim Öffnen färbt sich das <b>ganze Panel</b> um, damit du auf
        einen Blick siehst, in welchem Deck du bist (z.B. <b>rot = Dual-Stream</b>, blau = Solo). „(Globales Theme)" = folgt dem Standard.</p>
      {decks.length === 0 ? <p class="muted" style="font-size:13px">Keine Decks gefunden.</p> : (
        <div style="display:flex;flex-direction:column;gap:8px;max-width:560px">
          {decks.map((d) => (
            <div key={d.id} style="display:flex;align-items:center;gap:10px">
              <span style="font-size:18px">{d.icon || '🎛'}</span>
              <span style="flex:1;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{d.label || d.id}</span>
              {d.theme && d.theme.vars && <span title={d.theme.name}
                style={`width:15px;height:15px;flex:none;border-radius:4px;border:1px solid var(--line);background:${d.theme.vars['--accent'] || '#888'}`} />}
              <select style={selStyle} value={deckThemeValue(d)} onChange={(e) => setDeckTheme(d.id, e.currentTarget.value)}>
                <option value="">(Globales Theme)</option>
                {Object.keys(PRESETS).map((id) => <option value={id}>{PRESETS[id].name}</option>)}
                {customNames.length > 0 && <optgroup label="Eigene Themes">{customNames.map((nm) => <option value={'__custom:' + nm}>{nm}</option>)}</optgroup>}
              </select>
            </div>
          ))}
        </div>
      )}

      <h2 class="th-sec">Presets</h2>
      <div class="th-presets">
        {Object.keys(PRESETS).map((id) => (
          <button class={'th-preset' + (st.activeId === id ? ' on' : '')} onClick={() => applyPreset(id)} key={id}>
            <span class="th-name">{PRESETS[id].name}</span>
            <span class="th-sw">
              {['--bg', '--bg3', '--accent', '--accent2', '--fg'].map((k) => (
                <i key={k} style={`background:${PRESETS[id].vars[k]}`} />
              ))}
            </span>
          </button>
        ))}
      </div>

      <h2 class="th-sec">Eigene Farben <span class="muted" style="font-size:13px;font-weight:400">— aktiv: {activeName()}</span></h2>
      {lowContrast && (
        <p class="th-warn">⚠ Wenig Kontrast zwischen Hintergrund und Text ({cr.toFixed(1)}:1, empfohlen ≥ 4.5) — evtl. schlecht lesbar.</p>
      )}
      <div class="th-rows">
        {CORE_VARS.map(colorRow)}
        {adv && SEMANTIC_VARS.map(colorRow)}
      </div>
      <div class="th-actions">
        <button class="btn ghost small" onClick={() => setAdv((a) => !a)}>{adv ? 'Weniger' : 'Erweiterte Farben (OK/Warnung/Fehler/Live)'}</button>
        <button class="btn ghost small" onClick={reset}>Zurücksetzen (Slate)</button>
      </div>

      <h2 class="th-sec">Eigenes Theme speichern</h2>
      <div class="th-actions">
        <input class="reward-input" style="max-width:240px" placeholder="Theme-Name (z.B. Mein OLED)"
               value={name} onInput={(e) => setName(e.currentTarget.value)} />
        <button class="btn small" onClick={saveCustom}>Speichern</button>
        {msg && <span class="msg ok small">{msg}</span>}
      </div>
      {customNames.length > 0 && (
        <div class="th-mythemes">
          {customNames.map((nm) => (
            <div class="th-mt" key={nm}>
              <span class="th-sw" style="flex:none">
                {['--bg', '--accent', '--fg'].map((k) => <i key={k} style={`background:${st.customs[nm][k]}`} />)}
              </span>
              <span class="th-mt-name">{nm}</span>
              <button class="btn ghost tiny" onClick={() => applyCustom(nm)}>Anwenden</button>
              <button class="btn ghost tiny danger" onClick={() => deleteCustom(nm)}>Löschen</button>
            </div>
          ))}
        </div>
      )}

      <h2 class="th-sec">Teilen</h2>
      <div class="th-actions">
        <button class="btn ghost small" onClick={exportTheme}>Exportieren (.json)</button>
        <label class="btn ghost small" style="cursor:pointer;display:inline-flex;align-items:center">
          Importieren
          <input type="file" accept="application/json,.json" style="display:none" onChange={importTheme} />
        </label>
      </div>
    </div>
  )
}
