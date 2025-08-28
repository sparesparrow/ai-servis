package cz.aiservis.app.core.background

import cz.aiservis.app.core.networking.Backoff
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

interface BLEManager {
	suspend fun initialize()
	suspend fun disconnect()
	suspend fun connectWithRetry(deviceAddress: String): Boolean
}

@Singleton
class BLEManagerImpl @Inject constructor() : BLEManager {
	override suspend fun initialize() { /* no-op stub */ }
	override suspend fun disconnect() { /* no-op stub */ }

	private suspend fun tryConnect(address: String): Boolean {
		// Placeholder for integration with a BLE library (e.g., Nordic BLE Library):
		// this.connect(device)
		//   .retry(10, 250)
		//   .useAutoConnect(true)
		//   .timeout(24 * 3600 * 1000)
		//   .enqueue()
		// Return true on success when callback indicates connected.
		return false
	}

	override suspend fun connectWithRetry(deviceAddress: String): Boolean {
		val delays = Backoff.exponential(baseMs = 250, maxMs = 8000, attempts = 6)
		for (d in delays) {
			if (tryConnect(deviceAddress)) return true
			delay(d)
		}
		return false
	}
}
