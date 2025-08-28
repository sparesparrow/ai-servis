package cz.aiservis.app.core.background

data class HealthPing(
	val ts: Long = System.currentTimeMillis(),
	val appVersion: String = BuildConfig.VERSION_NAME,
	val status: String = "ok"
)
