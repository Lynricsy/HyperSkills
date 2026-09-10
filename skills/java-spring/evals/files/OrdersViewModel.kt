package com.example.mobile.orders

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch

class OrdersViewModel(
    private val repository: OrdersRepository,
) : ViewModel() {

    val uiState = MutableStateFlow(OrdersUiState())

    private val scope = CoroutineScope(Dispatchers.IO)

    fun refresh() {
        GlobalScope.launch(Dispatchers.IO) {
            val orders = repository.load()
            uiState.value = uiState.value.copy(orders = orders, loading = false)
        }
    }

    fun submit(orderId: Long) {
        scope.launch {
            repository.submit(orderId)
            refresh()
        }
    }
}

data class OrdersUiState(
    val orders: List<Order> = emptyList(),
    val loading: Boolean = true,
)
