package com.rigzdeck

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.GestureDetector
import android.view.MotionEvent
import android.view.View
import android.view.WindowManager
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

/**
 * Vollbild-WebView mit Multi-Host-Umschalter. Entdeckt alle Deck-Hosts automatisch per mDNS.
 * Das Deck fuellt den ganzen Bildschirm; die Host-Leiste liegt als Overlay darueber und ist
 * standardmaessig versteckt. Ein kleiner Griff (oben links) blendet sie ein/aus; "Vollbild"
 * blendet auch den Griff aus -> reines Deck, Rueckkehr per Wisch von oben nach unten / Zurueck.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var web: WebView
    private lateinit var overlay: View
    private lateinit var statusText: TextView
    private lateinit var tabBar: LinearLayout
    private lateinit var tabScroll: View
    private lateinit var handle: View
    private var barShown = false
    private var fullscreen = false
    private val handler = Handler(Looper.getMainLooper())
    private var discovery: Discovery? = null
    private val hosts = LinkedHashMap<String, HostInfo>()
    private var selectedKey: String? = null
    private var loaded = false

    private val settingsLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {
            reloadManualHosts()
            startDiscovery()           // Auto-Discovery evtl. umgeschaltet
            rebuildTabs()
            if (selectedKey == null || !hosts.containsKey(selectedKey)) autoSelect()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)  // Display bleibt an, solange die App offen ist
        web = findViewById(R.id.web)
        overlay = findViewById(R.id.statusOverlay)
        statusText = findViewById(R.id.statusText)
        tabBar = findViewById(R.id.tabBar)
        tabScroll = findViewById(R.id.tabScroll)
        handle = findViewById(R.id.handle)
        handle.setOnClickListener { setBar(!barShown) }
        findViewById<Button>(R.id.statusSettingsBtn).setOnClickListener { openSettings() }
        configureWeb()
        setupGestures()
        reloadManualHosts()
        rebuildTabs()
        startDiscovery()
        if (hosts.isNotEmpty()) autoSelect() else showStatus(getString(R.string.searching))
        handler.postDelayed({
            if (selectedKey == null && hosts.isEmpty()) showStatus(getString(R.string.not_found))
        }, 8000)
    }

    private fun reloadManualHosts() {
        hosts.filterValues { it.manual }.keys.toList().forEach { hosts.remove(it) }
        for (h in Settings(this).manualHosts()) hosts[h.key] = h
    }

    private fun startDiscovery() {
        discovery?.stop()
        discovery = null
        if (!Settings(this).autoDiscover) return
        discovery = Discovery(this,
            onFound = { h -> runOnUiThread { onHost(h) } },
            onLost = { key -> runOnUiThread { onHostLost(key) } })
        discovery?.start()
    }

    private fun onHost(h: HostInfo) {
        hosts[h.key] = h
        rebuildTabs()
        if (selectedKey == null) autoSelect()
    }

    private fun onHostLost(key: String) {
        val h = hosts[key] ?: return
        if (!h.manual) { hosts.remove(key); rebuildTabs() }
    }

    private fun autoSelect() {
        if (hosts.isEmpty()) return
        val last = Settings(this).lastHostKey
        selectHost(if (last.isNotBlank() && hosts.containsKey(last)) last else hosts.keys.first())
    }

    private fun selectHost(key: String) {
        val h = hosts[key] ?: return
        selectedKey = key
        Settings(this).lastHostKey = key
        loaded = false
        rebuildTabs()
        setBar(false)              // nach der Wahl klappt die Leiste wieder weg
        statusText.text = h.label
        overlay.visibility = View.GONE
        web.loadUrl(h.url())
    }

    private fun rebuildTabs() {
        tabBar.removeAllViews()
        val collapse = Button(this)
        collapse.text = "▲"
        collapse.isAllCaps = false
        collapse.minWidth = 0; collapse.minHeight = 0; collapse.setPadding(26, 12, 26, 12)
        collapse.setOnClickListener { setBar(false) }
        tabBar.addView(collapse)
        for ((key, h) in hosts) {
            val b = Button(this)
            b.text = h.label
            b.isAllCaps = false
            b.minWidth = 0; b.minHeight = 0
            b.setPadding(30, 12, 30, 12)
            b.alpha = if (key == selectedKey) 1f else 0.5f
            b.setOnClickListener { selectHost(key) }
            tabBar.addView(b)
        }
        val gear = Button(this)
        gear.text = "⚙"   // ⚙
        gear.minWidth = 0; gear.minHeight = 0; gear.setPadding(26, 12, 26, 12)
        gear.setOnClickListener { openSettings() }
        tabBar.addView(gear)
        val fs = Button(this)
        fs.text = getString(R.string.fullscreen_enter)
        fs.isAllCaps = false
        fs.minWidth = 0; fs.minHeight = 0; fs.setPadding(26, 12, 26, 12)
        fs.setOnClickListener { enterFullscreen() }
        tabBar.addView(fs)
    }

    private fun openSettings() =
        settingsLauncher.launch(Intent(this, SettingsActivity::class.java))

    /** Host-Leiste ein-/ausblenden. Der Griff ist sichtbar, solange die Leiste zu ist (und kein Vollbild). */
    private fun setBar(show: Boolean) {
        barShown = show
        tabScroll.visibility = if (show) View.VISIBLE else View.GONE
        handle.visibility = if (show || fullscreen) View.GONE else View.VISIBLE
    }

    private fun enterFullscreen() {
        fullscreen = true
        setBar(false)              // Leiste + Griff aus -> reines Deck
        Toast.makeText(this, R.string.fullscreen_hint, Toast.LENGTH_LONG).show()
    }

    private fun exitFullscreen() {
        fullscreen = false
        setBar(true)               // Leiste zeigen; Griff kommt zurueck, sobald man sie schliesst
    }

    /**
     * Wisch von oben nach unten (aus dem oberen Bildschirmrand) holt im Vollbild das Menue zurueck.
     * Der Listener verbraucht das Event NIE (return false) -> normale Deck-Tipps bleiben unberuehrt.
     */
    @SuppressLint("ClickableViewAccessibility")
    private fun setupGestures() {
        val gd = GestureDetector(this, object : GestureDetector.SimpleOnGestureListener() {
            override fun onScroll(e1: MotionEvent?, e2: MotionEvent, dx: Float, dy: Float): Boolean {
                if (fullscreen && e1 != null) {
                    val topEdge = resources.displayMetrics.heightPixels * 0.12f
                    val down = e2.y - e1.y
                    if (e1.y < topEdge && down > 140f && down > Math.abs(e2.x - e1.x)) {
                        runOnUiThread { exitFullscreen() }
                    }
                }
                return false
            }
        })
        web.setOnTouchListener { _, ev -> gd.onTouchEvent(ev); false }
    }

    private fun configureWeb() {
        val s = web.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.useWideViewPort = true
        s.loadWithOverviewMode = true
        s.mediaPlaybackRequiresUserGesture = false
        s.cacheMode = WebSettings.LOAD_DEFAULT
        web.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                if (url != null && url != "about:blank") { loaded = true; overlay.visibility = View.GONE }
            }
            override fun onReceivedError(view: WebView?, req: WebResourceRequest?, err: WebResourceError?) {
                if (req?.isForMainFrame == true) { loaded = false; showStatus(getString(R.string.connect_failed)) }
            }
        }
    }

    private fun showStatus(msg: String) { statusText.text = msg; overlay.visibility = View.VISIBLE }

    override fun onResume() { super.onResume(); immersive() }
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus); if (hasFocus) immersive()
    }

    @Suppress("DEPRECATION")
    private fun immersive() {
        window.decorView.systemUiVisibility = (
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY or View.SYSTEM_UI_FLAG_FULLSCREEN
                or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION)
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (fullscreen) exitFullscreen()
        else if (web.canGoBack()) web.goBack()
        else super.onBackPressed()
    }

    override fun onDestroy() { discovery?.stop(); super.onDestroy() }
}
