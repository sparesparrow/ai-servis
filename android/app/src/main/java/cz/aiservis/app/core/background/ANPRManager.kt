package cz.aiservis.app.core.background

import cz.aiservis.app.core.camera.AnprPostprocessor
import cz.aiservis.app.core.storage.PreferencesRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

interface ANPRManager {
	suspend fun startDetection()
	suspend fun stopDetection()
	val events: Flow<ANPREvent>
}

@Singleton
class ANPRManagerImpl @Inject constructor(
	private val prefs: PreferencesRepository
) : ANPRManager {
	private val _events = MutableSharedFlow<ANPREvent>(replay = 0)
	override val events: Flow<ANPREvent> = _events

	override suspend fun startDetection() { /* no-op stub */ }
	override suspend fun stopDetection() { /* no-op stub */ }

	// MVP helper to emit a processed event from a raw OCR result
	suspend fun emitRawOcr(rawText: String, baseConfidence: Float, snapshotId: String? = null) {
		val region = prefs.anprRegion.first()
		val (normPlate, bonus) = AnprPostprocessor.applyRegionHeuristics(rawText, region)
		val tuned = AnprPostprocessor.tuneConfidence(baseConfidence, bonus)
		_events.emit(ANPREvent(plateHash = normPlate, confidence = tuned, snapshotId = snapshotId))
	}
}

data class ANPREvent(
	val plateHash: String,
	val confidence: Float,
	val snapshotId: String? = null,
	val timestamp: Long = System.currentTimeMillis()
)
