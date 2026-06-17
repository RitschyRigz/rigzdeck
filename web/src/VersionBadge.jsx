import { useState, useEffect } from 'preact/hooks'

// Kleiner Versions-Marker in der Ecke — zeigt die LAUFENDE RigzDeck-Version, damit ein alter/falscher
// Build (z. B. eine alte v0.1.0, die von woanders autostartet) sofort auffällt. Quelle: /health.
export function VersionBadge() {
  const [v, setV] = useState('')
  useEffect(() => {
    fetch('/health')
      .then((r) => r.json())
      .then((d) => setV(d && d.version ? String(d.version) : ''))
      .catch(() => {})
  }, [])
  return <div class="rd-rev" title="Laufende RigzDeck-Version (aus /health)">RigzDeck v{v || '?'}</div>
}
