package com.example.messages.nav

import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navDeepLink
import androidx.navigation.toRoute
import kotlinx.serialization.Serializable

@Serializable data object Inbox
@Serializable data object ComposeMessage
@Serializable data object ContactPicker
@Serializable data class Conversation(val threadId: String)

@Composable
fun MessagesNavHost() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = Inbox) {
        composable<Inbox> {
            InboxScreen(
                onCompose = { navController.navigate(ComposeMessage) },
                onOpenThread = { id -> navController.navigate(Conversation(id)) },
            )
        }

        composable<ComposeMessage> {
            val viewModel: ComposeMessageViewModel = viewModel()
            val lifecycleOwner = LocalLifecycleOwner.current
            navController.currentBackStackEntry?.savedStateHandle
                ?.getLiveData<Contact>("picked_contact")
                ?.observe(lifecycleOwner) { contact -> viewModel.onRecipientSelected(contact) }

            ComposeMessageScreen(
                recipient = viewModel.recipient,
                onPickRecipient = { navController.navigate(ContactPicker) },
            )
        }

        composable<ContactPicker> {
            ContactPickerScreen(
                onContactSelected = { contact ->
                    navController.previousBackStackEntry?.savedStateHandle?.set("picked_contact", contact)
                    navController.popBackStack()
                },
            )
        }

        composable<Conversation>(
            deepLinks = listOf(
                navDeepLink { uriPattern = "https://messages.example.com/thread/{threadId}" },
            ),
        ) { entry ->
            ConversationScreen(threadId = entry.toRoute<Conversation>().threadId)
        }
    }
}
