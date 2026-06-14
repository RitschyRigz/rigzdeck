package com.rigzdeck

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.os.Handler
import android.os.Looper

/**
 * Findet den RigzDeck-Host im LAN per mDNS/NSD (`_rigzdeck._tcp.`). Beim ersten
 * aufgeloesten Treffer wird [onFound] mit Host-IP + Port aufgerufen. Kein IP-Eintippen noetig.
 */
class Discovery(context: Context, private val onFound: (String, Int) -> Unit) {

    private val nsd = context.applicationContext
        .getSystemService(Context.NSD_SERVICE) as NsdManager
    private val handler = Handler(Looper.getMainLooper())
    private var listener: NsdManager.DiscoveryListener? = null
    private var resolving = false
    private var done = false
    private var timeout: Runnable? = null

    companion object {
        const val SERVICE_TYPE = "_rigzdeck._tcp."
    }

    fun start(timeoutMs: Long, onTimeout: () -> Unit) {
        val l = object : NsdManager.DiscoveryListener {
            override fun onStartDiscoveryFailed(serviceType: String?, errorCode: Int) {}
            override fun onStopDiscoveryFailed(serviceType: String?, errorCode: Int) {}
            override fun onDiscoveryStarted(serviceType: String?) {}
            override fun onDiscoveryStopped(serviceType: String?) {}
            override fun onServiceLost(serviceInfo: NsdServiceInfo?) {}
            override fun onServiceFound(serviceInfo: NsdServiceInfo?) {
                if (serviceInfo == null || resolving || done) return
                if (serviceInfo.serviceType?.contains("rigzdeck") != true) return
                resolving = true
                resolve(serviceInfo)
            }
        }
        listener = l
        try {
            nsd.discoverServices(SERVICE_TYPE, NsdManager.PROTOCOL_DNS_SD, l)
        } catch (e: Exception) {
            // ignorieren -> Timeout greift
        }
        timeout = Runnable {
            if (!done) {
                stop()
                onTimeout()
            }
        }
        handler.postDelayed(timeout!!, timeoutMs)
    }

    @Suppress("DEPRECATION")
    private fun resolve(info: NsdServiceInfo) {
        try {
            nsd.resolveService(info, object : NsdManager.ResolveListener {
                override fun onResolveFailed(serviceInfo: NsdServiceInfo?, errorCode: Int) {
                    resolving = false
                }

                override fun onServiceResolved(serviceInfo: NsdServiceInfo?) {
                    if (done || serviceInfo == null) return
                    val host = serviceInfo.host?.hostAddress ?: run { resolving = false; return }
                    val port = serviceInfo.port
                    done = true
                    stop()
                    onFound(host, port)
                }
            })
        } catch (e: Exception) {
            resolving = false
        }
    }

    fun stop() {
        timeout?.let { handler.removeCallbacks(it) }
        timeout = null
        listener?.let {
            try {
                nsd.stopServiceDiscovery(it)
            } catch (e: Exception) {
                // schon gestoppt
            }
        }
        listener = null
    }
}
