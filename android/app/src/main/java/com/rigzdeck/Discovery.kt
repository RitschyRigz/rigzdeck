package com.rigzdeck

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.os.Handler
import android.os.Looper

/** Ein Deck-Host — entdeckt per mDNS oder manuell hinzugefügt. */
data class HostInfo(
    val key: String,
    val label: String,
    val host: String,
    val port: Int,
    val path: String = "/panel",
    val manual: Boolean = false,
) {
    fun url(): String = "http://$host:$port$path"
}

/**
 * Findet ALLE Deck-Hosts im LAN per mDNS (`_rigzdeck._tcp` — RigzDeck-Instanzen UND Cockpit).
 * Ruft [onFound] pro aufgelöstem Host, [onLost] beim Verschwinden. Auflösung läuft seriell,
 * da NSD nur eine gleichzeitige resolveService-Operation erlaubt.
 */
class Discovery(
    context: Context,
    private val onFound: (HostInfo) -> Unit,
    private val onLost: (String) -> Unit,
) {
    private val nsd = context.applicationContext.getSystemService(Context.NSD_SERVICE) as NsdManager
    private val handler = Handler(Looper.getMainLooper())
    private var listener: NsdManager.DiscoveryListener? = null
    private val pending = ArrayDeque<NsdServiceInfo>()
    private var resolving = false

    companion object { const val TYPE = "_rigzdeck._tcp." }

    fun start() {
        val l = object : NsdManager.DiscoveryListener {
            override fun onStartDiscoveryFailed(t: String?, e: Int) {}
            override fun onStopDiscoveryFailed(t: String?, e: Int) {}
            override fun onDiscoveryStarted(t: String?) {}
            override fun onDiscoveryStopped(t: String?) {}
            override fun onServiceFound(s: NsdServiceInfo) {
                if (s.serviceType?.contains("rigzdeck") == true) {
                    handler.post { pending.addLast(s); pump() }
                }
            }
            override fun onServiceLost(s: NsdServiceInfo) {
                val name = s.serviceName
                if (name != null) handler.post { onLost(name) }
            }
        }
        listener = l
        try { nsd.discoverServices(TYPE, NsdManager.PROTOCOL_DNS_SD, l) } catch (e: Exception) {}
    }

    @Suppress("DEPRECATION")
    private fun pump() {
        if (resolving || pending.isEmpty()) return
        resolving = true
        val s = pending.removeFirst()
        val rl = object : NsdManager.ResolveListener {
            override fun onResolveFailed(si: NsdServiceInfo?, e: Int) {
                handler.post { resolving = false; pump() }
            }
            override fun onServiceResolved(si: NsdServiceInfo) {
                handler.post {
                    val host = si.host?.hostAddress
                    if (host != null) {
                        val attrs = si.attributes ?: emptyMap<String, ByteArray>()
                        fun attr(k: String): String =
                            attrs[k]?.let { try { String(it) } catch (e: Exception) { "" } } ?: ""
                        val path = attr("path").ifBlank { "/panel" }
                        val name = si.serviceName ?: "$host:${si.port}"
                        val label = attr("app").ifBlank { name }
                        onFound(HostInfo(key = name, label = label, host = host, port = si.port, path = path))
                    }
                    resolving = false; pump()
                }
            }
        }
        try { nsd.resolveService(s, rl) } catch (e: Exception) { resolving = false; pump() }
    }

    fun stop() {
        listener?.let { try { nsd.stopServiceDiscovery(it) } catch (e: Exception) {} }
        listener = null
        pending.clear()
        resolving = false
    }
}
