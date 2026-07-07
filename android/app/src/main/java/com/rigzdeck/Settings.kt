package com.rigzdeck

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * Geräte-Einstellungen (SharedPreferences). Standard: Auto-Discovery AN, Port 7990 — läuft
 * ohne Eingabe. Zusätzlich eine Liste manuell hinzugefügter Hosts (z. B. Cockpit oder
 * Tailscale-IPs) und der zuletzt gewählte Host.
 */
class Settings(context: Context) {

    private val ctx = context.applicationContext
    private val p = ctx.getSharedPreferences("rigzdeck", Context.MODE_PRIVATE)

    init { seedDefaultsIfNeeded() }

    companion object {
        const val DEFAULT_PORT = 7990
        const val DEFAULT_PATH = "/panel"
    }

    /** Beim ALLERERSTEN Start (Prefs noch nie geschrieben) optionale, MITGELIEFERTE Standard-Hosts aus
     *  assets/default_hosts.json in die manuelle Liste uebernehmen. Das Asset ist im oeffentlichen Build
     *  NICHT vorhanden (gitignored) -> No-op/generisch; ein privater CI-Build (workflow_dispatch mit
     *  bake_hosts) brennt es aus einem Secret ein. Format = wie die gespeicherte manual-Liste
     *  ([{label,host,port,path}]). Der Nutzer kann die Eintraege danach normal bearbeiten/loeschen (sie
     *  liegen dann in den Prefs). Greift nur solange 'manual' fehlt -> nach 'Daten loeschen' erneut. */
    private fun seedDefaultsIfNeeded() {
        if (p.contains("manual")) return   // schon initialisiert (auch leere Liste) -> nie ueberschreiben
        try {
            val txt = ctx.assets.open("default_hosts.json").bufferedReader().use { it.readText() }.trim()
            if (txt.isBlank() || txt == "[]") return
            JSONArray(txt)                  // validieren (wirft bei Muell -> nichts seeden)
            p.edit().putString("manual", txt).apply()
        } catch (e: Exception) { /* kein Asset / kaputt -> generisch, nichts seeden */ }
    }

    var autoDiscover: Boolean
        get() = p.getBoolean("auto", true)
        set(v) { p.edit().putBoolean("auto", v).apply() }

    var lastHostKey: String
        get() = p.getString("lastKey", "") ?: ""
        set(v) { p.edit().putString("lastKey", v).apply() }

    fun manualHosts(): List<HostInfo> {
        val out = ArrayList<HostInfo>()
        try {
            val arr = JSONArray(p.getString("manual", "[]") ?: "[]")
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                val host = o.optString("host").trim()
                if (host.isBlank()) continue
                val port = o.optInt("port", DEFAULT_PORT)
                val label = o.optString("label").ifBlank { host }
                val path = o.optString("path").ifBlank { DEFAULT_PATH }
                out.add(HostInfo("manual:$host:$port", label, host, port, path, manual = true))
            }
        } catch (e: Exception) { /* leere/kaputte Liste -> nichts */ }
        return out
    }

    fun addManualHost(label: String, host: String, port: Int, path: String = DEFAULT_PATH) {
        val key = "manual:$host:$port"
        val list = manualHosts().filter { it.key != key }.toMutableList()
        list.add(HostInfo(key, label.ifBlank { host }, host, port, path, manual = true))
        saveManual(list)
    }

    fun removeManualHost(key: String) = saveManual(manualHosts().filter { it.key != key })

    private fun saveManual(list: List<HostInfo>) {
        val arr = JSONArray()
        for (h in list) {
            arr.put(JSONObject().put("label", h.label).put("host", h.host)
                .put("port", h.port).put("path", h.path))
        }
        p.edit().putString("manual", arr.toString()).apply()
    }
}
