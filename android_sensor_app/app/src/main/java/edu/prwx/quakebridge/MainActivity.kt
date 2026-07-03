package edu.prwx.quakebridge

import android.content.Context
import android.content.SharedPreferences
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Bundle
import android.text.InputType
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import java.io.IOException
import java.time.Instant
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sqrt

class MainActivity : AppCompatActivity(), SensorEventListener {
    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private lateinit var prefs: SharedPreferences
    private val httpClient = OkHttpClient()

    private var monitoring = false
    private var lastSentMs = 0L
    private var peakG = 0.0
    private var triggerCount = 0

    private lateinit var statusText: TextView
    private lateinit var peakText: TextView
    private lateinit var triggerText: TextView
    private lateinit var serverUrl: EditText
    private lateinit var latInput: EditText
    private lateinit var lonInput: EditText
    private lateinit var consentCheck: CheckBox
    private lateinit var startButton: Button

    private val triggerThresholdG = 0.18
    private val minSecondsBetweenSends = 15

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = getSharedPreferences("prwx_quake_bridge", Context.MODE_PRIVATE)
        sensorManager = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        buildUi()
        loadPrefs()
    }

    private fun buildUi() {
        val root = LinearLayout(this)
        root.orientation = LinearLayout.VERTICAL
        root.setPadding(28, 28, 28, 28)

        val title = TextView(this)
        title.text = "PR-WX Android Sensor Bridge"
        title.textSize = 24f
        title.setTypeface(null, 1)
        root.addView(title)

        val note = TextView(this)
        note.text = "Experimental: no predice terremotos. Envía señales anónimas y aproximadas al dashboard PR-WX para validación con fuentes oficiales."
        note.textSize = 15f
        note.setPadding(0, 8, 0, 16)
        root.addView(note)

        consentCheck = CheckBox(this)
        consentCheck.text = "Doy consentimiento para enviar señales aproximadas del acelerómetro, sin nombre, teléfono ni device ID."
        root.addView(consentCheck)

        root.addView(label("Servidor API"))
        serverUrl = EditText(this)
        serverUrl.hint = "http://10.0.2.2:8000"
        serverUrl.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
        root.addView(serverUrl)

        root.addView(label("Ubicación aproximada"))
        latInput = EditText(this)
        latInput.hint = "Latitud aproximada, ej. 18.02"
        latInput.inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL or InputType.TYPE_NUMBER_FLAG_SIGNED
        lonInput = EditText(this)
        lonInput.hint = "Longitud aproximada, ej. -66.61"
        lonInput.inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL or InputType.TYPE_NUMBER_FLAG_SIGNED
        root.addView(latInput)
        root.addView(lonInput)

        startButton = Button(this)
        startButton.text = "Activar monitoreo"
        startButton.setOnClickListener { toggleMonitoring() }
        root.addView(startButton)

        val testButton = Button(this)
        testButton.text = "Enviar prueba segura"
        testButton.setOnClickListener { sendTrigger(0.05, 0.35, "android_sensor_bridge_test") }
        root.addView(testButton)

        statusText = TextView(this)
        statusText.text = "Estado: detenido"
        statusText.textSize = 18f
        statusText.setPadding(0, 18, 0, 6)
        root.addView(statusText)

        peakText = TextView(this)
        peakText.text = "Pico g: 0.00"
        root.addView(peakText)

        triggerText = TextView(this)
        triggerText.text = "Triggers enviados: 0"
        root.addView(triggerText)

        val footer = TextView(this)
        footer.text = "Privacidad: no se guarda device ID. Toda señal debe validarse contra USGS/Red Sísmica antes de alertar."
        footer.setPadding(0, 20, 0, 0)
        root.addView(footer)

        setContentView(root)
    }

    private fun label(text: String): TextView {
        val tv = TextView(this)
        tv.text = text
        tv.setTypeface(null, 1)
        tv.setPadding(0, 12, 0, 2)
        return tv
    }

    private fun loadPrefs() {
        serverUrl.setText(prefs.getString("server_url", BuildConfig.DEFAULT_SERVER_URL))
        latInput.setText(prefs.getString("coarse_lat", "18.02"))
        lonInput.setText(prefs.getString("coarse_lon", "-66.61"))
        consentCheck.isChecked = prefs.getBoolean("consent", false)
    }

    private fun savePrefs() {
        prefs.edit()
            .putString("server_url", serverUrl.text.toString().trim())
            .putString("coarse_lat", latInput.text.toString().trim())
            .putString("coarse_lon", lonInput.text.toString().trim())
            .putBoolean("consent", consentCheck.isChecked)
            .apply()
    }

    private fun toggleMonitoring() {
        savePrefs()
        if (!consentCheck.isChecked) {
            toast("Debe aceptar consentimiento.")
            return
        }
        if (accelerometer == null) {
            toast("Este equipo no tiene acelerómetro disponible.")
            return
        }
        monitoring = !monitoring
        if (monitoring) {
            sensorManager.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_GAME)
            startButton.text = "Detener monitoreo"
            statusText.text = "Estado: monitoreando"
        } else {
            sensorManager.unregisterListener(this)
            startButton.text = "Activar monitoreo"
            statusText.text = "Estado: detenido"
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (!monitoring || event.sensor.type != Sensor.TYPE_ACCELEROMETER) return
        val ax = event.values[0].toDouble()
        val ay = event.values[1].toDouble()
        val az = event.values[2].toDouble()
        val total = sqrt(ax * ax + ay * ay + az * az)
        val dynamicG = abs(total - SensorManager.GRAVITY_EARTH) / SensorManager.GRAVITY_EARTH
        peakG = max(peakG, dynamicG)
        peakText.text = "Pico g: %.3f".format(peakG)

        val now = System.currentTimeMillis()
        val enoughTime = (now - lastSentMs) > minSecondsBetweenSends * 1000
        if (dynamicG >= triggerThresholdG && enoughTime) {
            val confidence = (dynamicG / 0.45).coerceIn(0.30, 0.95)
            sendTrigger(dynamicG, confidence, "android_sensor_bridge")
            lastSentMs = now
        }
    }

    private fun sendTrigger(pgaG: Double, confidence: Double, source: String) {
        if (!consentCheck.isChecked) {
            toast("Active consentimiento antes de enviar.")
            return
        }
        savePrefs()
        val base = serverUrl.text.toString().trim().trimEnd('/')
        val lat = latInput.text.toString().toDoubleOrNull()
        val lon = lonInput.text.toString().toDoubleOrNull()
        if (base.isEmpty() || lat == null || lon == null) {
            toast("Servidor, latitud y longitud aproximada son requeridos.")
            return
        }

        val body = """
            {
              "trigger_time_utc": "${Instant.now()}",
              "coarse_lat": $lat,
              "coarse_lon": $lon,
              "pga_g": ${"%.4f".format(pgaG)},
              "confidence": ${"%.3f".format(confidence)},
              "source": "$source"
            }
        """.trimIndent()

        val request = Request.Builder()
            .url("$base/seismic/android-trigger")
            .post(RequestBody.create("application/json; charset=utf-8".toMediaType(), body))
            .build()

        httpClient.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread { statusText.text = "Error enviando: ${e.message}" }
            }
            override fun onResponse(call: Call, response: Response) {
                val ok = response.isSuccessful
                response.close()
                runOnUiThread {
                    triggerCount += if (ok) 1 else 0
                    triggerText.text = "Triggers enviados: $triggerCount"
                    statusText.text = if (ok) "Trigger enviado" else "Servidor respondió error"
                }
            }
        })
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    override fun onDestroy() {
        sensorManager.unregisterListener(this)
        super.onDestroy()
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()
}
