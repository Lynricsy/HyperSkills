package com.example.chat.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier

data class Message(val id: String, val author: String, val preview: String, val body: String)

// Hosted by ChatActivity. AndroidManifest.xml today:
//   <activity android:name=".ChatActivity" android:exported="false" />
@Composable
fun ChatScreen(
    conversationId: String,
    messages: List<Message>,
    onSend: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    var draft by remember { mutableStateOf("") }
    var expandedIds by remember { mutableStateOf(setOf<String>()) }
    val listState = remember { LazyListState() }

    Column(modifier) {
        LazyColumn(state = listState, modifier = Modifier.weight(1f)) {
            items(messages, key = { it.id }) { message ->
                val expanded = message.id in expandedIds
                Column(
                    Modifier.clickable {
                        expandedIds = if (expanded) expandedIds - message.id else expandedIds + message.id
                    }
                ) {
                    Text(message.author)
                    Text(if (expanded) message.body else message.preview)
                }
            }
        }
        Row {
            TextField(value = draft, onValueChange = { draft = it }, modifier = Modifier.weight(1f))
            Button(onClick = { onSend(draft); draft = "" }) { Text("Send") }
        }
    }
}
