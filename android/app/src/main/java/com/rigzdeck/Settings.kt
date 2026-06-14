package com.rigzdeck

import android.content.Context

/**
 * Geraet-Einstellungen (SharedPreferences). Standard: Auto-Discovery AN, Port 7990 — so
 * laeuft die App ohne jede Eingabe. Manueller Host/Port nur als Override bei Bedarf.
 */
class Settings(context: Context) {

    private val p = context.applicationContext
        .getSharedPreferences("rigzdeck", Context.MODE_PRIVATE)

    companion object {
        const val DEFAULT_PORT = 7990
        const val DEFAULT_PATH = "/panel"
    }

    var autoDiscover: Boolean
        get() = p.getBoolean("auto", true)
        set(v) { p.edit().putBoolean("auto", v).apply() }

    var host: String
        get() = p.getString("host", "") ?: ""
        set(v) { p.edit().putString("host", v).apply() }

    var port: Int
        get() = p.getInt("port", DEFAULT_PORT)
        set(v) { p.edit().putInt("port", v).apply() }

    // Zuletzt automatisch gefundener Host — als schneller Fallback beim naechsten Start.
    var lastHost: String
        get() = p.getString("lastHost", "") ?: ""
        set(v) { p.edit().putString("lastHost", v).apply() }

    var lastPort: Int
        get() = p.getInt("lastPort", DEFAULT_PORT)
        set(v) { p.edit().putInt("lastPort", v).apply() }

    /** Baut die Panel-URL. Akzeptiert nackten Host, host:port oder eine volle http(s)-URL. */
    fun urlFor(host: String, port: Int): String {
        val h = host.trim()
        if (h.startsWith("http://") || h.startsWith("https://")) {
            return if (h.contains("/panel")) h else h.trimEnd('/') + DEFAULT_PATH
        }
        return "http://$h:$port$DEFAULT_PATH"
    }
}
