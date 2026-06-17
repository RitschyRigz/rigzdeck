import { useState, useEffect } from 'preact/hooks'

// Offline-Schirm fürs Tablet (aus dem Cockpit übernommen): pollt /health; bricht der PC/Server weg,
// kommt nach einer kurzen Schonfrist ein Vollbild-Overlay statt eines Browser-Fehlers — und blendet
// wieder aus, sobald der Server zurück ist. Die Schonfrist verhindert Flackern bei kurzem Neustart.
export function OfflineScreen() {
  const [offline, setOffline] = useState(false)
  useEffect(() => {
    let lastOk = Date.now()
    let alive = true
    const GRACE = 8000          // ms ohne Antwort, bevor der Schirm kommt (kurzer Neustart soll nicht flashen)
    const tick = async () => {
      const ctrl = new AbortController()
      const to = setTimeout(() => ctrl.abort(), 3000)
      try {
        const r = await fetch('/health', { signal: ctrl.signal, cache: 'no-store' })
        if (!r.ok) throw new Error('bad')
        lastOk = Date.now()
        if (alive) setOffline(false)
      } catch {
        if (alive && Date.now() - lastOk > GRACE) setOffline(true)
      } finally {
        clearTimeout(to)
      }
    }
    tick()
    const id = setInterval(tick, 4000)
    return () => { alive = false; clearInterval(id) }
  }, [])
  if (!offline) return null
  return (
    <div class="rd-offline">
      <div class="rd-offline-box">
        <span class="rd-offline-dot" />
        <h2>Offline</h2>
        <p>Verbindung zum PC verloren — warte auf Rückkehr …</p>
      </div>
    </div>
  )
}
