import SwiftUI

extension View {
    @ViewBuilder
    func `if`<Content: View>(_ condition: Bool, transform: (Self) -> Content) -> some View {
        if condition {
            transform(self)
        } else {
            self
        }
    }
}

struct PlaybackControls: View {
    var isCompact: Bool
    var isDimmed: Bool

    var body: some View {
        ZStack {
            Color.black

            VStack {
                Spacer()

                HStack(spacing: 24) {
                    Button("Previous", systemImage: "backward.fill") {}
                        .padding(12)
                        .glassEffect()
                        .opacity(isDimmed ? 0.6 : 1)

                    Button("Play", systemImage: "play.fill") {}
                        .padding(12)
                        .glassEffect()
                        .interactive()

                    Text("Now playing")
                        .padding(8)
                        .glassEffect(.regular, in: .rect(cornerRadius: 16))
                        .allowsHitTesting(false)
                }
                .if(isCompact) { $0.scaleEffect(0.8) }
                .padding(.bottom, 40)
            }
        }
    }
}
