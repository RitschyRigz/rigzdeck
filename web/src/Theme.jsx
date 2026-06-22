import { useState, useEffect } from 'preact/hooks'
import {
  CORE_VARS, SEMANTIC_VARS, PRESETS, DEFAULT_ID,
  loadLocal, saveLocal, resolveVars, applyVars, contrastRatio,
  fetchServerTheme, pushServerThemeDebounced,
} from './theme.js'
import { Glyph } from '@deckcore/icons.jsx'

// 🎨 Theme-Tab — RigzDeck personalisieren. Presets + Color-Picker pro Farbe + eigene
// Themes (speichern/teilen). Der Editor ist MASTER: Änderungen wirken sofort live UND
// werden als GETEILTES Theme auf den Server geschrieben → alle Geräte ohne eigenes
// Override folgen automatisch (z.B. das Tablet-Panel). deckcore bleibt unberührt.
export function Theme() {
  const initCustoms = loadLocal().customs
  const [st, setSt] = useState({ activeId: DEFAULT_ID, adhoc: null, customs: initCustoms })
  const [vars, setVars] = useState(() => resolveVars({ activeId: DEFAULT_ID, adhoc: null }, initCustoms))
  const [adv, setAdv] = useState(false)
  const [name, setName] = useState('')
  const [msg, setMsg] = useState('')

  // Beim Öffnen das aktuell geteilte (Server-)Theme laden, damit der Editor den echten Stand zeigt.
  useEffect(() => {
    let alive = true
    fetchServerTheme().then((srv) => {
      if (!alive || !srv || !srv.vars) return
      const nv = { ...PRESETS[DEFAULT_ID].vars, ...srv.vars }
      setSt((s) => ({ ...s, activeId: srv.activeId || '__adhoc', adhoc: srv.adhoc || null }))
      setVars(nv); applyVars(nv)
    })
    return () => { alive = false }
  }, [])

  // Wirkt sofort (live), merkt eigene Themes lokal, pusht das geteilte Theme (debounced) auf den Server.
  function commit(nextSt, nextVars) {
    setSt(nextSt); setVars(nextVars)
    applyVars(nextVars)
    saveLocal({ override: loadLocal().override, customs: nextSt.customs })
    pushServerThemeDebounced({ activeId: nextSt.activeId, adhoc: nextSt.adhoc, vars: nextVars })
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

  function exportTheme() {
    const data = JSON.stringify({ name: activeName(), vars }, null, 2)
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

  const colorRow = (v) => (
    <div class="th-row" key={v.key}>
      <label>{v.label}</label>
      <input type="color" value={vars[v.key]} onInput={(e) => editVar(v.key, e.currentTarget.value)} />
      <input type="text" value={vars[v.key]} spellcheck={false}
             onChange={(e) => editVar(v.key, e.currentTarget.value)} />
    </div>
  )

  const customNames = Object.keys(st.customs || {})

  return (
    <div class="th">
      <p class="hint">Personalisiere RigzDeck — wirkt sofort und gilt als <b>geteiltes Theme für alle Geräte</b>.
        Ein Tablet kann im Panel (🎨) lokal abweichen, z.B. OLED-Schwarz.</p>

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

      <h2 class="th-sec">Vorschau</h2>
      <div class="th-prev">
        <div class="th-prev-row">
          <div class="th-prev-tile"><span class="th-pi" style="color:var(--accent)"><Glyph name="play" /></span><span>Play</span></div>
          <div class="th-prev-tile"><span class="th-pi" style="color:var(--accent)"><Glyph name="volume-2" /></span><span>Vol</span></div>
          <div class="th-prev-tile"><span class="th-pi" style="color:var(--accent2)"><Glyph name="video" /></span><span>OBS</span></div>
          <div class="th-prev-tile acc"><span class="th-pi" style="color:var(--live)"><Glyph name="record" /></span><span>Live</span></div>
        </div>
        <p class="th-prev-cap muted">Die neuen SVG-Symbole folgen der Akzentfarbe — sie passen sich jedem Theme
          automatisch an. Symbole wählst du pro Taste im Deck-Editor („🎨 Symbol-Bibliothek").</p>
      </div>
    </div>
  )
}
