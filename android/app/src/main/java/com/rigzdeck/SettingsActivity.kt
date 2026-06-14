package com.rigzdeck

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/** Einstellungen: Auto-Discovery an/aus + manuelle Hosts (Cockpit, Tailscale-IPs …) verwalten. */
class SettingsActivity : AppCompatActivity() {

    private lateinit var cfg: Settings
    private lateinit var manualList: LinearLayout

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        cfg = Settings(this)
        setResult(Activity.RESULT_OK)   // jede Änderung -> MainActivity lädt Hosts neu

        val auto = findViewById<CheckBox>(R.id.autoDiscover)
        auto.isChecked = cfg.autoDiscover
        auto.setOnCheckedChangeListener { _, c -> cfg.autoDiscover = c }

        manualList = findViewById(R.id.manualList)
        val label = findViewById<EditText>(R.id.label)
        val host = findViewById<EditText>(R.id.host)
        val port = findViewById<EditText>(R.id.port)
        findViewById<Button>(R.id.add).setOnClickListener {
            val h = host.text.toString().trim()
            if (h.isNotBlank()) {
                val pt = port.text.toString().trim().toIntOrNull() ?: Settings.DEFAULT_PORT
                cfg.addManualHost(label.text.toString().trim(), h, pt)
                label.setText(""); host.setText(""); port.setText("")
                refreshManual()
            }
        }
        findViewById<Button>(R.id.done).setOnClickListener { finish() }
        refreshManual()
    }

    private fun refreshManual() {
        manualList.removeAllViews()
        for (h in cfg.manualHosts()) {
            val row = LinearLayout(this)
            row.orientation = LinearLayout.HORIZONTAL
            val t = TextView(this)
            t.text = "${h.label}  (${h.host}:${h.port})"
            t.setTextColor(0xFFE7E9EE.toInt())
            t.layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            val del = Button(this)
            del.text = "✕"   // ✕
            del.isAllCaps = false
            del.setOnClickListener { cfg.removeManualHost(h.key); refreshManual() }
            row.addView(t); row.addView(del)
            manualList.addView(row)
        }
    }
}
