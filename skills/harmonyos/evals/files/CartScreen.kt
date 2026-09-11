// app/src/main/kotlin/com/example/shop/cart/CartScreen.kt
// Android app, Jetpack Compose. The quantity stepper does not refresh the total
// and the list loses scroll position whenever a line is removed.

package com.example.shop.cart

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow

data class LineItem(var sku: String, var qty: Int, val price: Int)

class CartViewModel : ViewModel() {
    val lines = MutableStateFlow(mutableListOf<LineItem>())
    fun bump(item: LineItem, delta: Int) {
        item.qty += delta
    }
}

@Composable
fun CartScreen(vm: CartViewModel) {
    val lines by vm.lines.collectAsState()
    val total = remember { mutableStateOf(0) }

    Column {
        LazyColumn {
            items(lines) { line ->
                QtyStepper(line, vm)
            }
        }
        Text("total ${total.value}")
    }
}

@Composable
private fun QtyStepper(line: LineItem, vm: CartViewModel) {
    Row {
        Button(onClick = { vm.bump(line, -1) }) { Text("-") }
        Text("${line.qty}")
        Button(onClick = { vm.bump(line, +1) }) { Text("+") }
    }
}
