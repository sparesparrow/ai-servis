package cz.aiservis.app.core.background

import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import javax.inject.Inject
import javax.inject.Singleton

interface OBDManager {
	val obdData: Flow<OBDData>
	suspend fun startMonitoring()
	suspend fun stopMonitoring()
	fun setSamplingMode(mode: SamplingMode)
}

@Singleton
class OBDManagerImpl @Inject constructor() : OBDManager {
	private val _obdData = MutableSharedFlow<OBDData>(replay = 0)
	override val obdData: Flow<OBDData> = _obdData

	@Volatile
	private var samplingMode: SamplingMode = SamplingMode.NORMAL

	override suspend fun startMonitoring() { /* no-op stub */ }
	override suspend fun stopMonitoring() { /* no-op stub */ }

	override fun setSamplingMode(mode: SamplingMode) {
		samplingMode = mode
		// In a real implementation, adjust PID polling intervals based on mode
	}
}
