package com.example.pantry.scan

import android.content.ContentResolver
import android.graphics.Bitmap
import android.graphics.ImageDecoder
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.pantry.ml.LabelClassifier
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

// minSdk 29. LabelClassifier wraps a native interpreter handle; close() must run or the
// native memory (~40 MB) leaks for the life of the process.
@HiltViewModel
class LabelScanViewModel @Inject constructor(
    private val resolver: ContentResolver,
    private val classifier: LabelClassifier,
    @DefaultDispatcher private val defaultDispatcher: CoroutineDispatcher,
) : ViewModel() {

    private val _label = MutableStateFlow<String?>(null)
    val label: StateFlow<String?> = _label.asStateFlow()

    fun onPhotoPicked(uri: Uri) {
        viewModelScope.launch {
            _label.value = withContext(defaultDispatcher) { classify(uri) }
        }
    }

    private suspend fun classify(uri: Uri): String {
        val source = ImageDecoder.createSource(resolver, uri)
        val decoded = ImageDecoder.decodeBitmap(source)
        val input = Bitmap.createScaledBitmap(decoded, 224, 224, true)
        val pixels = IntArray(224 * 224)
        input.getPixels(pixels, 0, 224, 0, 0, 224, 224)
        return classifier.classify(pixels)
    }

    override fun onCleared() {
        viewModelScope.launch {
            classifier.close()
        }
        super.onCleared()
    }
}
