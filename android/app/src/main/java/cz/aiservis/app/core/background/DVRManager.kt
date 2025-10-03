package cz.aiservis.app.core.background

import android.content.Context
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import cz.aiservis.app.data.db.ClipEntity
import cz.aiservis.app.data.db.ClipsDao
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton
import dagger.hilt.android.qualifiers.ApplicationContext

interface DVRManager {
    val clipEvents: SharedFlow<ClipEvent>
    fun startRecording()
    fun stopRecording()
    fun triggerEventClip(reason: String)
    fun isRecording(): Boolean
}

data class ClipEvent(
    val type: ClipEventType,
    val clipId: Long? = null,
    val reason: String? = null
)

enum class ClipEventType {
    RECORDING_STARTED,
    RECORDING_STOPPED,
    EVENT_CLIP_SAVED,
    BUFFER_FULL,
    OFFLOAD_READY
}

@Singleton
class DVRManagerImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val clipsDao: ClipsDao,
    private val coroutineScope: CoroutineScope
) : DVRManager {

    private val _clipEvents = MutableSharedFlow<ClipEvent>()
    override val clipEvents = _clipEvents.asSharedFlow()

    @Volatile
    private var isRecordingActive = false
    private val rollingBufferSize = 60_000 // 60 seconds in ms
    private val maxClipSize = 30_000_000L // 30MB max clip size

    override fun startRecording() {
        if (isRecordingActive) return

        isRecordingActive = true

        // Schedule periodic offload work
        scheduleOffloadWork()

        coroutineScope.launch {
            _clipEvents.emit(ClipEvent(ClipEventType.RECORDING_STARTED))
        }
    }

    override fun stopRecording() {
        if (!isRecordingActive) return

        isRecordingActive = false

        coroutineScope.launch {
            _clipEvents.emit(ClipEvent(ClipEventType.RECORDING_STOPPED))
        }
    }

    override fun triggerEventClip(reason: String) {
        if (!isRecordingActive) return

        coroutineScope.launch(Dispatchers.IO) {
            try {
                // Create clip entity (placeholder - real implementation would capture video)
                val clipPath = generateClipPath(reason)
                val clip = ClipEntity(
                    ts = System.currentTimeMillis(),
                    reason = reason,
                    filePath = clipPath,
                    durationMs = rollingBufferSize,
                    sizeBytes = maxClipSize,
                    offloaded = false
                )

                clipsDao.insert(clip)

                _clipEvents.emit(
                    ClipEvent(
                        type = ClipEventType.EVENT_CLIP_SAVED,
                        clipId = clip.id,
                        reason = reason
                    )
                )
            } catch (e: Exception) {
                // Log error in real implementation
            }
        }
    }

    override fun isRecording(): Boolean = isRecordingActive

    private fun generateClipPath(reason: String): String {
        val timestamp = System.currentTimeMillis()
        val sanitizedReason = reason.replace(Regex("[^a-zA-Z0-9]"), "_")
        return "clips/${timestamp}_${sanitizedReason}.mp4"
    }

    private fun scheduleOffloadWork() {
        val offloadWork = PeriodicWorkRequestBuilder<DvrOffloadWorker>(
            1, TimeUnit.HOURS // Check for offload every hour
        ).build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "dvr_offload_work",
            ExistingPeriodicWorkPolicy.KEEP,
            offloadWork
        )
    }
}
