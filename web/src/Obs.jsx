import { useState, useEffect } from 'preact/hooks'

// 🎬 OBS-Tab — RigzDeck spricht OBS DIREKT über obs-websocket an (kein weiteres Programm nötig).
// Hier wird nur die Verbindung konfiguriert (Host/Port/Passwort, lokal gespeichert). Die OBS-
// Buttons selbst (Szene wechseln, Quelle ein-/ausblenden, Stream/Aufnahme) baust du im Deck-Tab
// als Aktion „🎬 OBS" — die Szenen-/Quellennamen erscheinen dort als Vorschläge, sobald verbunden.
export function Obs() {
  const [host, setHost] = useState('127.0.0.1')
  const [port, setPort] = useState(4455)
  const [password, setPassword] = useState('')
  const [hasPw, setHasPw] = useState(false)
  const [status, setStatus] = useState(null)   // {available, connected, error, obs_version}
  const [scenes, setScenes] = useState(null)    // Szenen-Namen, wenn verbunden
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  async function refreshScenes() {
    try {
      const d = await (await fetch('/api/obs/scenes')).json()
      setScenes(Array.isArray(d.scenes) ? d.scenes : [])
    } catch (e) { setScenes(null) }
  }

  function applyStatus(d) {
    setStatus(d); setHasPw(!!d.has_password)
    if (d.connected) { setMsg('Verbunden ✓'); refreshScenes() }
    else { setMsg(d.error || ''); setScenes(null) }
  }

  // Beim Öffnen den gespeicherten Stand + aktuelle Verbindung laden.
  useEffect(() => {
    let alive = true
    fetch('/api/obs/config').then((r) => r.json()).then((d) => {
      if (!alive) return
      setHost(d.host || '127.0.0.1'); setPort(d.port || 4455); setHasPw(!!d.has_password)
      setStatus({ available: d.available, connected: d.connected })
      if (d.connected) refreshScenes()
    }).catch(() => {})
    return () => { alive = false }
  }, [])

  async function save() {
    setBusy(true); setMsg('')
    // Passwort nur senden, wenn etwas eingegeben wurde — leer = unverändert (kein versehentliches Löschen).
    const body = { host: (host || '').trim() || '127.0.0.1', port: Number(port) || 4455 }
    if ((password || '').trim() !== '') body.password = password
    try {
      const d = await (await fetch('/api/obs/config', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      })).json()
      setPassword('')   // nie im Klartext im Feld stehen lassen
      applyStatus(d)
    } catch (e) { setMsg('Fehler beim Speichern'); setStatus({ available: true, connected: false }) }
    setBusy(false)
  }

  async function test() {
    setBusy(true); setMsg('')
    try {
      applyStatus(await (await fetch('/api/obs/status?probe=true')).json())
    } catch (e) { setMsg('Fehler beim Testen') }
    setBusy(false)
  }

  const connected = !!(status && status.connected)
  const available = !status || status.available !== false
  const badge = !available ? { t: 'nicht enthalten', c: 'err' }
    : connected ? { t: 'Verbunden', c: 'ok' } : { t: 'Nicht verbunden', c: 'idle' }

  return (
    <div class="th">
      <p class="hint">RigzDeck steuert OBS <b>direkt</b> über obs-websocket — kein Cockpit, kein
        Zusatzprogramm. In OBS: <b>Werkzeuge → WebSocket-Server-Einstellungen</b> → Server aktivieren
        (Standard-Port 4455) und das dort angezeigte Passwort hier eintragen.</p>

      <h2 class="th-sec">Verbindung <span class={'obs-badge ' + badge.c}>{badge.t}</span></h2>
      {!available && (
        <p class="th-warn">Die OBS-Unterstützung (obsws-python) ist in diesem Build nicht enthalten.</p>
      )}
      <div class="reward-row"><span class="muted conn-label">Host</span>
        <input class="reward-input" value={host} spellcheck={false} placeholder="127.0.0.1"
               onInput={(e) => setHost(e.currentTarget.value)} /></div>
      <div class="reward-row"><span class="muted conn-label">Port</span>
        <input class="reward-input" type="number" value={port} placeholder="4455"
               onInput={(e) => setPort(e.currentTarget.value)} /></div>
      <div class="reward-row"><span class="muted conn-label">Passwort</span>
        <input class="reward-input" type="password" value={password} spellcheck={false}
               placeholder={hasPw ? '•••••• gespeichert (leer = unverändert)' : 'OBS-WebSocket-Passwort'}
               onInput={(e) => setPassword(e.currentTarget.value)} /></div>

      <div class="th-actions">
        <button class="btn small" disabled={busy} onClick={save}>{busy ? '…' : 'Speichern & Verbinden'}</button>
        <button class="btn ghost small" disabled={busy} onClick={test}>Verbindung testen</button>
        {msg && <span class={'msg small ' + (connected ? 'ok' : 'err')}>{msg}</span>}
      </div>

      {connected && (
        <>
          <h2 class="th-sec">Status</h2>
          <p class="hint">
            {status.obs_version ? 'OBS ' + status.obs_version + ' · ' : ''}
            {scenes == null ? 'Szenen werden geladen…'
              : scenes.length + ' Szene' + (scenes.length === 1 ? '' : 'n') + ' gefunden'}
            {scenes && scenes.length > 0 && (
              <span class="muted"> — z.B. {scenes.slice(0, 4).join(', ')}{scenes.length > 4 ? ' …' : ''}</span>
            )}
          </p>
          <p class="hint">Jetzt im <b>Deck</b>-Tab OBS-Buttons anlegen (Aktion „🎬 OBS"): Szene wechseln,
            Quelle ein-/ausblenden, Stream/Aufnahme. Mit „🎬 OBS-Szenen importieren" legst du für jede
            Szene direkt einen Button an.</p>
        </>
      )}
    </div>
  )
}
