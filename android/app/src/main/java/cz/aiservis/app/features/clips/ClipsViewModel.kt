package cz.aiservis.app.features.clips

import androidx.lifecycle.ViewModel
import cz.aiservis.app.data.db.ClipEntity
import cz.aiservis.app.data.repositories.EventRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

@HiltViewModel
class ClipsViewModel @Inject constructor(
    private val eventRepository: EventRepository
) : ViewModel() {
    
    val clips: Flow<List<ClipEntity>> = eventRepository.getClips()
}
