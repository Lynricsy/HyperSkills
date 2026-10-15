import SwiftUI

// Deployment target: iOS 17.0. The project uses a hand-written Info.plist
// (GENERATE_INFOPLIST_FILE = NO); LedgerInfo.plist is that file.

struct Entry: Identifiable, Hashable {
    let id: UUID
    var title: String
    var amount: Decimal
}

@main
struct LedgerApp: App {
    var body: some Scene {
        WindowGroup {
            AppRootView()
        }
    }
}

struct AppRootView: View {
    @Environment(\.horizontalSizeClass) private var sizeClass

    var body: some View {
        // Product wants the sidebar presentation on wide iPhones too.
        TabView {
            Tab("Entries", systemImage: "list.bullet") { EntriesView() }
            Tab("Reports", systemImage: "chart.bar") { ReportsView() }
            Tab("Settings", systemImage: "gear") { SettingsView() }
        }
        .tabViewStyle(.sidebarAdaptable)
    }
}

struct EntriesView: View {
    @Environment(\.horizontalSizeClass) private var sizeClass
    @State private var entries: [Entry] = []

    var body: some View {
        if sizeClass != .compact {
            HStack {
                list
                DetailPlaceholder()
            }
        } else {
            list
        }
    }

    private var list: some View {
        List {
            ForEach(Array(entries.enumerated()), id: \.element.id) { index, entry in
                Text("\(index + 1). \(entry.title)")
            }
        }
    }
}

struct DetailPlaceholder: View {
    var body: some View { Text("Select an entry") }
}

struct ReportsView: View {
    var body: some View { Text("Reports") }
}

struct SettingsView: View {
    var body: some View { Text("Settings") }
}
