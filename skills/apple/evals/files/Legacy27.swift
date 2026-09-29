import SwiftUI

// Deployment target: iOS 17. The team is switching to Xcode 27 (iOS 27 SDK).

struct PulseModifier: AnimatableModifier {
    var scale: CGFloat

    var animatableData: CGFloat {
        get { scale }
        set { scale = newValue }
    }

    func body(content: Content) -> some View {
        content.scaleEffect(scale)
    }
}

struct PhotoViewer: View {
    let photo: Photo
    @Environment(\.presentationMode) private var presentationMode

    var body: some View {
        NavigationStack {
            ZoomableImage(photo: photo)
                .statusBarHidden(true)
                .navigationBarHidden(true)
                .onTapGesture { presentationMode.wrappedValue.dismiss() }
        }
    }
}

struct QuantityStepper: View {
    @State private var count: Int = 1

    init(initialCount: Int) {
        self.count = initialCount
    }

    var body: some View {
        Stepper("Quantity: \(count)", value: $count, in: 1...99)
    }
}

struct AlbumList: View {
    let albums: [Album]
    @State private var albumToDelete: Album?
    @State private var showDeleteConfirmation = false

    var body: some View {
        List(albums) { album in
            Text(album.title)
                .swipeActions {
                    Button("Delete", role: .destructive) {
                        albumToDelete = album
                        showDeleteConfirmation = true
                    }
                }
        }
        .confirmationDialog(
            "Delete album?",
            isPresented: $showDeleteConfirmation,
            presenting: albumToDelete
        ) { album in
            Button("Delete \(album.title)", role: .destructive) { delete(album) }
        }
    }
}
