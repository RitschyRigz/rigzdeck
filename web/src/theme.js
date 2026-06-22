// RigzDeck Theme-Engine — CSS-Variablen-Themes, Synced + Override.
// Ein GETEILTES Theme liegt auf dem Server (/api/theme). Jedes Gerät kann ein LOKALES
// Override setzen (localStorage); Override gewinnt, sonst folgt das Gerät dem Server-Theme.
// Der Editor ist Master (schreibt aufs Server-Theme); das Touch-Panel kann pro Gerät
// abweichen (z.B. OLED nur fürs Tablet). deck.css (deckcore) ist var-getrieben → wir
// setzen nur die :root-Variablen.

// Die personalisierbaren Variablen (Reihenfolge = Anzeige im Editor).
export const CORE_VARS = [
  { key: '--bg',      label: 'Hintergrund' },
  { key: '--bg2',     label: 'Fläche' },
  { key: '--bg3',     label: 'Kachel' },
  { key: '--line',    label: 'Linien / Rahmen' },
  { key: '--fg',      label: 'Text' },
  { key: '--muted',   label: 'Text gedämpft' },
  { key: '--accent',  label: 'Akzent' },
  { key: '--accent2', label: 'Akzent 2' },
]
export const SEMANTIC_VARS = [
  { key: '--ok',   label: 'OK / Grün' },
  { key: '--warn', label: 'Warnung' },
  { key: '--err',  label: 'Fehler' },
  { key: '--live', label: 'Live' },
]
export const ALL_VARS = [...CORE_VARS, ...SEMANTIC_VARS]

// Kuratierte Presets. Jedes liefert ALLE Variablen (sonst greift der Slate-Fallback).
export const PRESETS = {
  slate: { name: 'Slate Purple', vars: {
    '--bg': '#15171c', '--bg2': '#1c1f26', '--bg3': '#232733', '--line': '#2e3340',
    '--fg': '#e7e9ee', '--muted': '#8b93a4', '--accent': '#8a5cff', '--accent2': '#4ea1ff',
    '--ok': '#3ecf8e', '--warn': '#ffb454', '--err': '#ff6b6b', '--live': '#ff4d6d' } },
  cyan: { name: 'Cyan Rig', vars: {
    '--bg': '#0e1116', '--bg2': '#141b25', '--bg3': '#172231', '--line': '#24364a',
    '--fg': '#e8eef5', '--muted': '#8a9bb3', '--accent': '#22d3ee', '--accent2': '#3b82f6',
    '--ok': '#3ecf8e', '--warn': '#ffb454', '--err': '#ff6b6b', '--live': '#ff4d6d' } },
  green: { name: 'Signal Green', vars: {
    '--bg': '#0d1210', '--bg2': '#121c16', '--bg3': '#16241b', '--line': '#244232',
    '--fg': '#e6f1ea', '--muted': '#8aa595', '--accent': '#34d399', '--accent2': '#22d3ee',
    '--ok': '#3ecf8e', '--warn': '#ffb454', '--err': '#ff6b6b', '--live': '#ff5d6d' } },
  amber: { name: 'Amber Forge', vars: {
    '--bg': '#16110b', '--bg2': '#1e1710', '--bg3': '#261c10', '--line': '#3d2c14',
    '--fg': '#f2e9dd', '--muted': '#b09a82', '--accent': '#ff9e3d', '--accent2': '#ffb454',
    '--ok': '#3ecf8e', '--warn': '#ffcf6b', '--err': '#ff6b6b', '--live': '#ff4d6d' } },
  oled: { name: 'OLED-Schwarz', vars: {
    '--bg': '#000000', '--bg2': '#0a0a0a', '--bg3': '#151515', '--line': '#2c2c2c',
    '--fg': '#ffffff', '--muted': '#9aa0aa', '--accent': '#22d3ee', '--accent2': '#8a5cff',
    '--ok': '#3ecf8e', '--warn': '#ffb454', '--err': '#ff6b6b', '--live': '#ff4d6d' } },
  gold: { name: 'RitschyRigz Gold', vars: {
    '--bg': '#0d0b07', '--bg2': '#15110a', '--bg3': '#1d180d', '--line': '#3a2f17',
    '--fg': '#f5ecd8', '--muted': '#b09a6e', '--accent': '#e8b34a', '--accent2': '#d4943a',
    '--ok': '#3ecf8e', '--warn': '#ffcf6b', '--err': '#ff6b6b', '--live': '#ff4d6d' } },
  crimson: { name: 'Crimson', vars: {
    '--bg': '#120a0c', '--bg2': '#1a0e11', '--bg3': '#241317', '--line': '#45222a',
    '--fg': '#f3e6e8', '--muted': '#b58a90', '--accent': '#ef4444', '--accent2': '#f87171',
    '--ok': '#3ecf8e', '--warn': '#ffb454', '--err': '#ff5d5d', '--live': '#ff2f5e' } },
  synthwave: { name: 'Synthwave', vars: {
    '--bg': '#0f0a1e', '--bg2': '#160d2b', '--bg3': '#1f1338', '--line': '#3a2566',
    '--fg': '#f5e9ff', '--muted': '#9d8ad0', '--accent': '#ff4ecd', '--accent2': '#36e0ff',
    '--ok': '#2bd9a6', '--warn': '#ffb454', '--err': '#ff5d8a', '--live': '#ff2f9e' } },
  nord: { name: 'Nord', vars: {
    '--bg': '#242933', '--bg2': '#2e3440', '--bg3': '#3b4252', '--line': '#4c566a',
    '--fg': '#eceff4', '--muted': '#9aa4b8', '--accent': '#88c0d0', '--accent2': '#81a1c1',
    '--ok': '#a3be8c', '--warn': '#ebcb8b', '--err': '#bf616a', '--live': '#d08770' } },
  dracula: { name: 'Dracula', vars: {
    '--bg': '#21222c', '--bg2': '#282a36', '--bg3': '#343746', '--line': '#44475a',
    '--fg': '#f8f8f2', '--muted': '#9ca0b0', '--accent': '#bd93f9', '--accent2': '#ff79c6',
    '--ok': '#50fa7b', '--warn': '#f1fa8c', '--err': '#ff5555', '--live': '#ff79c6' } },
  rose: { name: 'Rosé', vars: {
    '--bg': '#160f13', '--bg2': '#1e141a', '--bg3': '#281b22', '--line': '#46303c',
    '--fg': '#f7e9f0', '--muted': '#c096aa', '--accent': '#fb7185', '--accent2': '#f472b6',
    '--ok': '#3ecf8e', '--warn': '#ffb454', '--err': '#ff6b6b', '--live': '#ff4d8d' } },
  mint: { name: 'Mint', vars: {
    '--bg': '#0a1413', '--bg2': '#0f1c1a', '--bg3': '#142523', '--line': '#21433d',
    '--fg': '#e3f3ef', '--muted': '#88aaa3', '--accent': '#2dd4bf', '--accent2': '#34d399',
    '--ok': '#34d399', '--warn': '#ffcf6b', '--err': '#ff6b6b', '--live': '#ff4d6d' } },
  mono: { name: 'Mono', vars: {
    '--bg': '#101012', '--bg2': '#17171a', '--bg3': '#202024', '--line': '#313137',
    '--fg': '#ededf0', '--muted': '#8b8b93', '--accent': '#d4d4dc', '--accent2': '#a0a0aa',
    '--ok': '#8fd6a8', '--warn': '#d8c48a', '--err': '#d68a8a', '--live': '#d68aa0' } },
}
export const DEFAULT_ID = 'slate'

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
  if (local.override) { applyVars(resolveVars(local.override, local.customs)); return }
  const srv = await fetchServerTheme()
  applyVars(srv && srv.vars ? { ...PRESETS[DEFAULT_ID].vars, ...srv.vars } : { ...PRESETS[DEFAULT_ID].vars })
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
