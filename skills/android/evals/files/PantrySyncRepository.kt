// shared/src/commonMain/kotlin/com/example/pantry/sync/PantrySyncRepository.kt
//
// This PR adds the web client: shared/build.gradle.kts now declares
//   kotlin { androidLibrary { ... }; iosArm64(); iosSimulatorArm64(); wasmJs { browser() } }
// with kotlinx-coroutines-core 1.10.2 in commonMain.dependencies.
package com.example.pantry.sync

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.IO
import kotlinx.coroutines.withContext

class PantrySyncRepository(
    private val api: PantryApi,
    private val store: PantryStore,
) {
    suspend fun sync(): Int = withContext(Dispatchers.IO) {
        val remote = api.fetchItems()
        store.replaceAll(remote)
        remote.size
    }
}

interface PantryApi { suspend fun fetchItems(): List<PantryItem> }
interface PantryStore { suspend fun replaceAll(items: List<PantryItem>) }
data class PantryItem(val id: String, val name: String, val quantity: Int)
