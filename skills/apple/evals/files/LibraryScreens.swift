import SwiftUI
import UIKit

// Deployment target: iOS 26. Building with Xcode 27.1 beta.

struct SettingsRootView: View {
    var body: some View {
        NavigationStack {
            List {
                NavigationLink("Account", value: SettingsPage.account)
                NavigationLink("Playback", value: SettingsPage.playback)
                NavigationLink("Downloads", value: SettingsPage.downloads)
                NavigationLink("Notifications", value: SettingsPage.notifications)
            }
            .navigationTitle("Settings")
            .navigationDestination(for: SettingsPage.self) { page in
                SettingsDetail(page: page)
            }
        }
    }
}

struct DashboardView: View {
    let cards: [DashboardCard]

    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                ForEach(cards) { card in
                    CardView(card: card)
                        .frame(maxWidth: UIScreen.main.bounds.width - 32)
                }
            }
            .padding()
        }
    }
}

struct NowPlayingView: View {
    @State private var progress = 0.0

    var body: some View {
        if UIDevice.current.userInterfaceIdiom == .pad || UIScreen.main.bounds.width > 700 {
            HStack {
                ArtworkView()
                PlayerControls(progress: $progress)
            }
        } else {
            VStack {
                ArtworkView()
                PlayerControls(progress: $progress)
            }
        }
    }
}

actor ThumbnailRenderer {
    func thumbnail(for data: Data, pointSize: CGSize) async -> UIImage? {
        let scale = await UIScreen.main.scale
        let maxPixel = max(pointSize.width, pointSize.height) * scale
        return downsample(data, maxPixel: maxPixel)
    }
}
