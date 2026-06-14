package com.rigzdeck

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

/**
 * Vollbild-WebView, das das RigzDeck-Panel des Hosts laedt. Der Host wird per mDNS
 * automatisch im Netzwerk gefunden (zero-config) — nur wenn das scheitert, muss der
 * Nutzer in den Einstellungen eine Adresse eingeben. Standard-Port 7990.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var overlay: View
    private lateinit var statusText: TextView
    private var discovery: Discovery? = null
    private var loaded = false
    private var currentUrl: String? = null

    private val settingsLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            loaded = false
            currentUrl = null
            connect()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        web = findViewById(R.id.web)
        overlay = findViewById(R.id.statusOverlay)
        statusText = findViewById(R.id.statusText)
        findViewById<Button>(R.id.settingsBtn).setOnClickListener { openSettings() }
        findViewById<Button>(R.id.statusSettingsBtn).setOnClickListener { openSettings() }
        configureWeb()
        connect()
    }

    private fun openSettings() =
        settingsLauncher.launch(Intent(this, SettingsActivity::class.java))

    private fun configureWeb() {
        val s = web.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true                 // Theme nutzt localStorage
        s.useWideViewPort = true
        s.loadWithOverviewMode = true
        s.mediaPlaybackRequiresUserGesture = false
        s.cacheMode = WebSettings.LOAD_DEFAULT
        web.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                if (url != null && url != "about:blank") {
                    loaded = true
                    overlay.visibility = View.GONE
                }
            }

            override fun onReceivedError(
                view: WebView?, request: WebResourceRequest?, error: WebResourceError?
            ) {
                if (request?.isForMainFrame == true) {
                    loaded = false
                    showStatus(getString(R.string.connect_failed))
                }
            }
        }
    }

    private fun connect() {
        val cfg = Settings(this)
        if (!cfg.autoDiscover && cfg.host.isNotBlank()) {
            load(cfg.urlFor(cfg.host, cfg.port))
            return
        }
        showStatus(getString(R.string.searching))
        discovery?.stop()
        discovery = Discovery(this) { host, port ->
            runOnUiThread {
                cfg.lastHost = host
                cfg.lastPort = port
                load(cfg.urlFor(host, port))
            }
        }
        discovery?.start(7000L) {
            runOnUiThread {
                if (loaded) return@runOnUiThread
                val last = cfg.lastHost
                if (last.isNotBlank()) load(cfg.urlFor(last, cfg.lastPort))
                else showStatus(getString(R.string.not_found))
            }
        }
    }

    private fun load(url: String) {
        if (loaded && url == currentUrl) return
        currentUrl = url
        web.loadUrl(url)
    }

    private fun showStatus(msg: String) {
        statusText.text = msg
        overlay.visibility = View.VISIBLE
    }

    override fun onResume() {
        super.onResume()
        immersive()
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus) immersive()
    }

    @Suppress("DEPRECATION")
    private fun immersive() {
        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                or View.SYSTEM_UI_FLAG_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            )
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (web.canGoBack()) web.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        discovery?.stop()
        super.onDestroy()
    }
}
