package cz.aiservis.app.core.background

import android.app.Notification
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Binder
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.lifecycle.LifecycleService
import androidx.lifecycle.lifecycleScope
import cz.aiservis.app.AIServisApplication.Companion.CHANNEL_DRIVING_SERVICE
import cz.aiservis.app.MainActivity
import cz.aiservis.app.R
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class DrivingService : LifecycleService() {

    @Inject
    lateinit var bleManager: BLEManager

    @Inject
    lateinit var mqttManager: MQTTManager

    @Inject
    lateinit var obdManager: OBDManager

    @Inject
    lateinit var anprManager: ANPRManager

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val binder = DrivingServiceBinder()

    private val _serviceState = MutableStateFlow(ServiceState.STOPPED)
    val serviceState: StateFlow<ServiceState> = _serviceState.asStateFlow()

    private val _vehicleData = MutableStateFlow(VehicleData())
    val vehicleData: StateFlow<VehicleData> = _vehicleData.asStateFlow()

    override fun onCreate() {
        super.onCreate()
        startForeground(NOTIFICATION_ID, createNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        super.onStartCommand(intent, flags, startId)
        
        when (intent?.action) {
            ACTION_START -> startService()
            ACTION_STOP -> stopService()
            ACTION_PAUSE -> pauseService()
            ACTION_RESUME -> resumeService()
        }
        
        return START_STICKY
    }

    override fun onBind(intent: Intent): IBinder {
        super.onBind(intent)
        return binder
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceScope.cancel()
        stopForeground(true)
    }

    private fun startService() {
        _serviceState.value = ServiceState.STARTING
        
        serviceScope.launch {
            try {
                // Initialize managers
                bleManager.initialize()
                mqttManager.connect()
                obdManager.startMonitoring()
                anprManager.startDetection()
                
                _serviceState.value = ServiceState.RUNNING
                
                // Start data collection
                collectVehicleData()
                
            } catch (e: Exception) {
                _serviceState.value = ServiceState.ERROR
            }
        }
    }

    private fun stopService() {
        _serviceState.value = ServiceState.STOPPING
        
        serviceScope.launch {
            try {
                bleManager.disconnect()
                mqttManager.disconnect()
                obdManager.stopMonitoring()
                anprManager.stopDetection()
                
                _serviceState.value = ServiceState.STOPPED
                stopSelf()
                
            } catch (e: Exception) {
                _serviceState.value = ServiceState.ERROR
            }
        }
    }

    private fun pauseService() {
        _serviceState.value = ServiceState.PAUSED
        // Pause data collection but keep connections alive
    }

    private fun resumeService() {
        _serviceState.value = ServiceState.RUNNING
        // Resume data collection
    }

    private suspend fun collectVehicleData() {
        // Collect OBD data
        obdManager.obdData.collect { obdData ->
            _vehicleData.value = _vehicleData.value.copy(
                fuelLevel = obdData.fuelLevel,
                engineRpm = obdData.engineRpm,
                vehicleSpeed = obdData.vehicleSpeed,
                coolantTemp = obdData.coolantTemp,
                engineLoad = obdData.engineLoad,
                dtcCodes = obdData.dtcCodes
            )
            
            // Publish to MQTT
            mqttManager.publishVehicleTelemetry(obdData)
            
            // Check for alerts
            checkAlerts(obdData)
        }
    }

    private fun checkAlerts(obdData: OBDData) {
        val alerts = mutableListOf<VehicleAlert>()
        
        if (obdData.fuelLevel < 20) {
            alerts.add(VehicleAlert(
                severity = AlertSeverity.WARNING,
                code = "FUEL_LOW",
                message = "Palivo dochází. Nejbližší čerpačka 4km."
            ))
        }
        
        if (obdData.coolantTemp > 105) {
            alerts.add(VehicleAlert(
                severity = AlertSeverity.CRITICAL,
                code = "ENGINE_OVERHEAT",
                message = "POZOR! Motor přehřívá. Zastavte bezpečně."
            ))
        }
        
        if (alerts.isNotEmpty()) {
            alerts.forEach { alert ->
                mqttManager.publishAlert(alert)
                showAlertNotification(alert)
            }
        }
    }

    private fun showAlertNotification(alert: VehicleAlert) {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val notification = NotificationCompat.Builder(this, CHANNEL_ALERTS)
            .setContentTitle("AI-SERVIS Alert")
            .setContentText(alert.message)
            .setSmallIcon(R.drawable.ic_alert)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        
        notificationManager.notify(alert.hashCode(), notification)
    }

    private fun createNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        return NotificationCompat.Builder(this, CHANNEL_DRIVING_SERVICE)
            .setContentTitle("AI-SERVIS Active")
            .setContentText("Driving assistance is running")
            .setSmallIcon(R.drawable.ic_car)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    inner class DrivingServiceBinder : Binder() {
        fun getService(): DrivingService = this@DrivingService
    }

    companion object {
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ALERTS = "alerts"
        
        const val ACTION_START = "cz.aiservis.app.START_DRIVING_SERVICE"
        const val ACTION_STOP = "cz.aiservis.app.STOP_DRIVING_SERVICE"
        const val ACTION_PAUSE = "cz.aiservis.app.PAUSE_DRIVING_SERVICE"
        const val ACTION_RESUME = "cz.aiservis.app.RESUME_DRIVING_SERVICE"
    }
}

enum class ServiceState {
    STOPPED, STARTING, RUNNING, PAUSED, STOPPING, ERROR
}

enum class AlertSeverity {
    LOW, WARNING, ERROR, CRITICAL
}

data class VehicleData(
    val fuelLevel: Int = 0,
    val engineRpm: Int = 0,
    val vehicleSpeed: Int = 0,
    val coolantTemp: Int = 0,
    val engineLoad: Int = 0,
    val dtcCodes: List<String> = emptyList()
)

data class VehicleAlert(
    val severity: AlertSeverity,
    val code: String,
    val message: String,
    val timestamp: Long = System.currentTimeMillis()
)

data class OBDData(
    val fuelLevel: Int,
    val engineRpm: Int,
    val vehicleSpeed: Int,
    val coolantTemp: Int,
    val engineLoad: Int,
    val dtcCodes: List<String>
)

