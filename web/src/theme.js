// RigzDeck Theme-Engine — CSS-Variablen-Themes, Synced + Override.
// Ein GETEILTES Theme liegt auf dem Server (/api/theme). Jedes Gerät kann ein LOKALES
// Override setzen (localStorage); Override gewinnt, sonst folgt das Gerät dem Server-Theme.
// Der Editor ist Master (schreibt aufs Server-Theme); das Touch-Panel kann pro Gerät
// abweichen (z.B. OLED nur fürs Tablet). deck.css (deckcore) ist var-getrieben → wir
// setzen nur die :root-Variablen.

// Variablen + Paletten kommen aus der GETEILTEN Single-Source (deckcore/web/themes.js) → Cockpit + RigzDeck
// + der per-Deck-Theme-Editor nutzen dieselben Themes. Hier nur in die hier erwartete Form gebracht.
import { THEME_VARS, THEME_PRESETS, DEFAULT_THEME_ID } from '@deckcore/themes.js'
export const CORE_VARS = THEME_VARS.filter((v) => v.core)
export const SEMANTIC_VARS = THEME_VARS.filter((v) => !v.core)
export const ALL_VARS = THEME_VARS
export const PRESETS = Object.fromEntries(THEME_PRESETS.map((p) => [p.id, { name: p.name, vars: p.vars }]))
export const DEFAULT_ID = DEFAULT_THEME_ID

// Globale „Look"-Einstellungen jenseits der Farben: Kachel-Stil-Default · Druck-Bestätigung (Modus + Farbe) ·
// Ordner-Rahmen (an/aus + Farbe). Teil des GETEILTEN Themes (synct auf alle Geräte). Defaults = wie bisher.
export const DEFAULT_LOOK = { tile: 'brackets', press: 'ring', pressColor: 'accent2', folder: true, folderColor: '#c8a44e' }
const _THEME_KW = ['accent', 'accent2', 'ok', 'warn', 'err', 'live']
// Theme-Schlüsselwort → CSS-Variable (folgt dem Theme), sonst die rohe Farbe (Hex).
export const colorVal = (c) => _THEME_KW.indexOf(c) >= 0 ? `var(--${c})` : (c || '')

const KEY = 'rd.theme'           // { override: {activeId, adhoc}|null, customs:{name:vars} }
const VARS_KEY = 'rd.theme.vars' // flacher {var:val}-Snapshot der aktiven Vars (Pre-Paint-Script)

// — Lokaler Gerätezustand (Override + eigene Themes) —
export function loadLocal() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || '{}')
    return { override: s.override || null, customs: s.customs || {} }
  } catch (e) {
    return { override: null, customs: {} }
  }
}
export function saveLocal(local) {
  try { localStorage.setItem(KEY, JSON.stringify(local)) } catch (e) { /* Speicher voll/blockiert */ }
}

// Auswahl {activeId, adhoc} (+ eigene Themes) → konkrete Variablen (immer auf Slate aufsetzen).
export function resolveVars(sel, customs) {
  const base = PRESETS[DEFAULT_ID].vars
  if (!sel) return { ...base }
  const id = sel.activeId
  if (id === '__adhoc' && sel.adhoc) return { ...base, ...sel.adhoc }
  if (id && id.indexOf('__custom:') === 0) {
    const nm = id.slice('__custom:'.length)
    if (customs && customs[nm]) return { ...base, ...customs[nm] }
  }
  if (PRESETS[id]) return { ...base, ...PRESETS[id].vars }
  return { ...base }
}

// Variablen auf :root anwenden + Snapshot fürs Pre-Paint-Script schreiben.
export function applyVars(vars) {
  const root = document.documentElement
  for (const k in vars) root.style.setProperty(k, vars[k])
  try { localStorage.setItem(VARS_KEY, JSON.stringify(vars)) } catch (e) { /* egal */ }
}

// „Look"-Einstellungen anwenden: Kachel-Stil-Default + Druck-Modus als body-data-Attribute (deckcore/deck.css
// liest sie generisch), Druck-/Ordner-Farben + Ordner-Rahmenbreite als CSS-Variablen. deckcore bleibt unberührt.
export function applyLook(look) {
  const lk = { ...DEFAULT_LOOK, ...(look || {}) }
  try {
    const root = document.documentElement, body = document.body
    body.dataset.tilestyle = lk.tile || 'brackets'
    body.dataset.press = lk.press || 'ring'
    root.style.setProperty('--press', colorVal(lk.pressColor) || 'var(--accent2)')
    root.style.setProperty('--folder-w', lk.folder === false ? '0' : '2px')
    root.style.setProperty('--folder', colorVal(lk.folderColor) || '#c8a44e')
  } catch (e) { /* headless / kein DOM */ }
}

// — Server (geteiltes Theme) —
export async function fetchServerTheme() {
  try {
    const r = await fetch('/api/theme')
    if (!r.ok) return null
    const d = await r.json()
    return d && d.vars ? d : null
  } catch (e) { return null }
}
export async function pushServerTheme(payload) {
  try {
    await fetch('/api/theme', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    })
  } catch (e) { /* offline / nicht erreichbar — lokal wirkt es trotzdem */ }
}
let _pushTimer = null
export function pushServerThemeDebounced(payload, ms = 500) {
  if (_pushTimer) clearTimeout(_pushTimer)
  _pushTimer = setTimeout(() => { _pushTimer = null; pushServerTheme(payload) }, ms)
}

// Beim App-Start (main.jsx + touch-main.jsx): lokales Override gewinnt, sonst Server-Theme,
// sonst Default. Async — das Pre-Paint-Script hat den letzten Snapshot schon angewandt (kein Flackern).
export async function initTheme() {
  const local = loadLocal()
  const srv = await fetchServerTheme()   // immer holen — auch für die globalen „Look"-Einstellungen
  // Farben: lokales Geräte-Override gewinnt (z.B. OLED), sonst das geteilte Server-Theme, sonst Default.
  if (local.override) applyVars(resolveVars(local.override, local.customs))
  else applyVars(srv && srv.vars ? { ...PRESETS[DEFAULT_ID].vars, ...srv.vars } : { ...PRESETS[DEFAULT_ID].vars })
  // Look (Kachel-Stil-Default / Druck / Ordner): global vom Server (oder Defaults).
  applyLook(srv && srv.look)
}

// WCAG-Kontrastverhältnis zweier #rrggbb-Farben (für den Lesbarkeits-Guard). null = ungültig.
export function contrastRatio(hex1, hex2) {
  const lum = (hex) => {
    const c = String(hex || '').replace('#', '')
    if (c.length !== 6) return null
    const ch = [0, 2, 4].map((i) => {
      const v = parseInt(c.slice(i, i + 2), 16) / 255
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)
    })
    if (ch.some((x) => Number.isNaN(x))) return null
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]
  }
  const l1 = lum(hex1), l2 = lum(hex2)
  if (l1 == null || l2 == null) return null
  const hi = Math.max(l1, l2), lo = Math.min(l1, l2)
  return (hi + 0.05) / (lo + 0.05)
}
