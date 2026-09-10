package com.example.news.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

@Immutable
data class Article(
    val id: String,
    val title: String,
    var readCount: Int,
    val tags: MutableList<String>,
)

class NewsViewModel(private val repo: NewsRepository) : ViewModel() {
    private val _articles = MutableStateFlow<List<Article>>(emptyList())
    val articles: StateFlow<List<Article>> = _articles.asStateFlow()

    val liveBanner: Flow<String> = repo.bannerTicker()

    fun refresh() {
        viewModelScope.launch { _articles.value = repo.load() }
    }

    fun markRead(article: Article) {
        article.readCount = article.readCount + 1
        _articles.value = _articles.value.toList()
    }
}

@Composable
fun NewsScreen(viewModel: NewsViewModel, scrollProgress: Float) {
    val articles by viewModel.articles.collectAsState()
    val listState = rememberLazyListState()
    val showJumpToTop = listState.firstVisibleItemIndex > 5

    Column {
        BannerBar(viewModel.liveBanner)

        if (showJumpToTop) {
            Text("Jump to top")
        }

        LazyColumn(
            state = listState,
            modifier = Modifier.offset(y = (scrollProgress * 24).dp),
        ) {
            items(articles) { article ->
                ArticleRow(
                    article = article,
                    allArticles = articles,
                    onClick = { viewModel.markRead(article) },
                )
            }
        }
    }
}

@Composable
private fun BannerBar(banner: Flow<String>) {
    val text by banner.collectAsState(initial = "")
    Text(text)
}

@Composable
private fun ArticleRow(
    article: Article,
    allArticles: List<Article>,
    onClick: () -> Unit,
) {
    val position = allArticles.indexOf(article)
    Column(
        modifier = Modifier
            .clickable(onClick = onClick)
            .padding(16.dp)
            .background(Color.LightGray),
    ) {
        Text("${position + 1}. ${article.title}")
        Text("read ${article.readCount} times")
    }
}

interface NewsRepository {
    suspend fun load(): List<Article>
    fun bannerTicker(): Flow<String>
}
