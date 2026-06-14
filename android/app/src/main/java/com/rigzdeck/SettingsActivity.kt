package com.rigzdeck

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import androidx.appcompat.app.AppCompatActivity

/** Einfache Einstellungen: Auto-Discovery an/aus + optionaler manueller Host/Port. */
class SettingsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        val cfg = Settings(this)
        val auto = findViewById<CheckBox>(R.id.autoDiscover)
        val host = findViewById<EditText>(R.id.host)
        val port = findViewById<EditText>(R.id.port)

        auto.isChecked = cfg.autoDiscover
        host.setText(cfg.host)
        port.setText(cfg.port.toString())

        findViewById<Button>(R.id.save).setOnClickListener {
            cfg.autoDiscover = auto.isChecked
            cfg.host = host.text.toString().trim()
            cfg.port = port.text.toString().trim().toIntOrNull() ?: Settings.DEFAULT_PORT
            setResult(Activity.RESULT_OK)
            finish()
        }
        findViewById<Button>(R.id.cancel).setOnClickListener { finish() }
    }
}
