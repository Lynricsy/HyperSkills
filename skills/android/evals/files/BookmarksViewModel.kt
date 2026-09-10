package com.example.shop.bookmarks

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class Bookmark(val id: Long, val url: String, val title: String)

@Dao
interface BookmarkDao {
    @Query("SELECT * FROM bookmarks ORDER BY created_at DESC LIMIT :limit")
    fun observeRecent(limit: Int): Flow<List<Bookmark>>

    @Query("SELECT COUNT(*) FROM bookmarks WHERE url LIKE '%' || :host || '%'")
    suspend fun countForHost(host: String): Int

    @Insert
    suspend fun insert(bookmark: Bookmark)
}

class BookmarksRepository(private val dao: BookmarkDao) {
    fun recent(): Flow<List<Bookmark>> = dao.observeRecent(limit = 50)
    suspend fun add(url: String, title: String) = dao.insert(Bookmark(0, url, title))
}

data class BookmarksUiState(
    val items: List<Bookmark> = emptyList(),
    val isEmpty: Boolean = true,
)

class BookmarksViewModel(private val repository: BookmarksRepository) : ViewModel() {

    val uiState: StateFlow<BookmarksUiState> =
        repository.recent()
            .map { BookmarksUiState(items = it, isEmpty = it.isEmpty()) }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(5_000),
                initialValue = BookmarksUiState(),
            )

    fun addBookmark(url: String, title: String) {
        viewModelScope.launch { repository.add(url, title) }
    }
}
