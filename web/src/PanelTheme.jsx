import { useState } from 'preact/hooks'
import { PRESETS, DEFAULT_ID, loadLocal, saveLocal, resolveVars, applyVars, fetchServerTheme } from './theme.js'

// 🎨 Kompakter Theme-Knopf fürs Touch-Panel. Setzt ein LOKALES Override NUR für dieses Gerät
// (z.B. OLED-Schwarz fürs Tablet) — oder „Folgt PC" = kein Override, folgt dem geteilten
// Server-Theme. Bewusst minimal (Presets + Folgt-PC); volle Anpassung lebt im Editor.
export function PanelTheme() {
  const [open, setOpen] = useState(false)
  const [local, setLocal] = useState(() => loadLocal())
  const overrideId = local.override ? local.override.activeId : null

  function pickPreset(id) {
    const nl = { ...local, override: { activeId: id, adhoc: null } }
    saveLocal(nl); setLocal(nl)
    applyVars(resolveVars(nl.override, nl.customs))
  }
  async function followPc() {
    const nl = { ...local, override: null }
    saveLocal(nl); setLocal(nl)
    const srv = await fetchServerTheme()
    applyVars(srv && srv.vars ? { ...PRESETS[DEFAULT_ID].vars, ...srv.vars } : { ...PRESETS[DEFAULT_ID].vars })
  }

  return (
    <div class="pt">
      <button class="pt-btn" onClick={() => setOpen((o) => !o)} title="Theme">🎨</button>
      {open && (
        <div class="pt-pop">
          <div class="pt-h">Theme <span class="muted">(dieses Gerät)</span></div>
          <button class={'pt-opt' + (!overrideId ? ' on' : '')} onClick={followPc}>↺ Folgt PC (Standard)</button>
          <div class="pt-presets">
            {Object.keys(PRESETS).map((id) => (
              <button class={'pt-preset' + (overrideId === id ? ' on' : '')} onClick={() => pickPreset(id)} key={id}>
                <span class="pt-sw">{['--bg', '--accent', '--fg'].map((k) => <i key={k} style={`background:${PRESETS[id].vars[k]}`} />)}</span>
                <span>{PRESETS[id].name}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
