// Snapshot app — deployment target iOS 18, building with Xcode 27 (iOS 27 SDK).
// Written from our WWDC25 session notes; it no longer builds on CI.
import SwiftUI
import UniformTypeIdentifiers

struct Photo: Identifiable, Codable, Transferable {
    let id: UUID
    var caption: String

    static var transferRepresentation: some TransferRepresentation {
        CodableRepresentation(contentType: .json)
    }
}

struct RootTabs: View {
    let photos: [Photo]

    var body: some View {
        if #available(iOS 26.0, *) {
            TabView {
                Tab("Library", systemImage: "photo.on.rectangle") {
                    LibraryGrid(photos: photos)
                }
                Tab(role: .search) {
                    SearchScreen()
                }
            }
        } else {
            TabView {
                LibraryGrid(photos: photos)
                    .tabItem { Label("Library", systemImage: "photo.on.rectangle") }
                SearchScreen()
                    .tabItem { Label("Search", systemImage: "magnifyingglass") }
            }
        }
    }
}

struct LibraryGrid: View {
    let photos: [Photo]
    @Namespace private var composeNamespace
    @State private var isComposing = false

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 110))]) {
                    ForEach(photos) { photo in
                        Text(photo.caption)
                            .frame(height: 110)
                    }
                }
            }
            .modifier(MultiItemDrag(photos: photos))
            .navigationTitle("Library")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Compose", systemImage: "square.and.pencil") {
                        isComposing = true
                    }
                    .navigationTransitionSource(id: "compose", namespace: composeNamespace)
                }
            }
            .sheet(isPresented: $isComposing) {
                ComposeSheet()
                    .navigationTransitionDestination(id: "compose", namespace: composeNamespace)
            }
        }
    }
}

/// Lets people drag several selected photos out at once.
struct MultiItemDrag: ViewModifier {
    let photos: [Photo]

    func body(content: Content) -> some View {
        if #available(iOS 26.0, *) {
            content.dragContainer(for: Photo.self) { ids in
                photos.filter { ids.contains($0.id) }
            }
        } else {
            content
        }
    }
}

struct ComposeSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var exposure = 0.0

    var body: some View {
        VStack(spacing: 20) {
            if #available(iOS 26.0, *) {
                Slider(value: $exposure, in: -2...2) {
                    Text("Exposure")
                }
                .sliderNeutralValue(0)
            } else {
                Slider(value: $exposure, in: -2...2) {
                    Text("Exposure")
                }
            }
            postButton
        }
        .padding(24)
        .background(.thinMaterial, in: .rect(cornerRadius: 24, style: .concentric))
        .overlay(alignment: .topTrailing) {
            // Design: 24×24 pt meets the WCAG 2.2 target-size minimum, so this is fine.
            Button {
                dismiss()
            } label: {
                Image(systemName: "xmark")
                    .frame(width: 24, height: 24)
            }
            .contentShape(.rect)
        }
    }

    @ViewBuilder private var postButton: some View {
        if #available(iOS 26.0, *) {
            Button("Post") {}
                .buttonStyle(.borderedProminent)
                .controlSize(.extraLarge)
        } else {
            Button("Post") {}
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
        }
    }
}

struct SearchScreen: View {
    @State private var query = ""

    var body: some View {
        NavigationStack {
            List {}
                .searchable(text: $query)
                .navigationTitle("Search")
        }
    }
}
