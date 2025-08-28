package cz.aiservis.app

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject

@HiltAndroidApp
class AIServisApplication : Application(), Configuration.Provider {

    @Inject
    lateinit var workerFactory: HiltWorkerFactory

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            // Driving Service Channel
            val drivingChannel = NotificationChannel(
                CHANNEL_DRIVING_SERVICE,
                "AI-SERVIS Driving Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Foreground service for AI-SERVIS driving assistance"
                setShowBadge(false)
            }

            // Alerts Channel
            val alertsChannel = NotificationChannel(
                CHANNEL_ALERTS,
                "AI-SERVIS Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Vehicle alerts and notifications"
                enableVibration(true)
                enableLights(true)
            }

            // ANPR Channel
            val anprChannel = NotificationChannel(
                CHANNEL_ANPR,
                "AI-SERVIS ANPR",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "License plate recognition notifications"
                setShowBadge(true)
            }

            notificationManager.createNotificationChannels(
                listOf(drivingChannel, alertsChannel, anprChannel)
            )
        }
    }

    override fun getWorkManagerConfiguration(): Configuration {
        return Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .build()
    }

    companion object {
        const val CHANNEL_DRIVING_SERVICE = "driving_service"
        const val CHANNEL_ALERTS = "alerts"
        const val CHANNEL_ANPR = "anpr"
    }
}

