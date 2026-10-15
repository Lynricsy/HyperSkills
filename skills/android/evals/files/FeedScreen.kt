package com.example.feed.ui

import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn

// Lives in the :core:model module (no Compose compiler there).
data class Comment(val id: Long, val author: String, val body: String)

data class Post(
    val id: Long,
    val title: String,
    val likeCount: Int,
    val tags: List<String>,
    // Typically 50-400 entries per post.
    val comments: List<Comment>,
)

data class FeedUiState(val posts: List<PostUi> = emptyList())

data class PostUi(
    val id: Long,
    val title: String,
    val likeCount: Int,
    val tags: List<String>,
    val comments: List<Comment>,
)

class FeedViewModel(repo: FeedRepository) : ViewModel() {
    // observePosts() re-emits the whole feed (about 3,000 posts) whenever any like count changes.
    val uiState: StateFlow<FeedUiState> = repo.observePosts()
        .map { posts ->
            FeedUiState(
                posts = posts.map { post ->
                    PostUi(
                        id = post.id,
                        title = post.title,
                        likeCount = post.likeCount,
                        tags = post.tags.toList(),
                        comments = post.comments.toList(),
                    )
                },
            )
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), FeedUiState())
}

@Composable
fun FeedScreen(viewModel: FeedViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    LazyColumn {
        items(state.posts) { post ->
            PostCard(post)
        }
    }
}

@Composable
private fun PostCard(post: PostUi) {
    Column {
        Text(post.title)
        Text("${post.likeCount} likes")
        Row { post.tags.forEach { Text("#$it") } }
        CommentPreview(post.comments)
    }
}

@Composable
private fun CommentPreview(comments: List<Comment>) {
    comments.take(2).forEach { Text("${it.author}: ${it.body}") }
}

interface FeedRepository {
    fun observePosts(): kotlinx.coroutines.flow.Flow<List<Post>>
}
