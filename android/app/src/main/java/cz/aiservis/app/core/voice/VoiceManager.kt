package cz.aiservis.app.core.voice

import javax.inject.Inject
import javax.inject.Singleton

interface VoiceManager {
	suspend fun speak(text: String)
}

@Singleton
class VoiceManagerImpl @Inject constructor() : VoiceManager {
	override suspend fun speak(text: String) { /* no-op stub for TTS */ }
}
