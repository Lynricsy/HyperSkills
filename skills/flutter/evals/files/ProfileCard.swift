import SwiftUI

struct Profile: Identifiable {
    let id: UUID
    let name: String
    let followers: Int
}

struct ProfileCard: View {
    @State var profile: Profile
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(profile.name)
                .font(.headline)
            Text("\(profile.followers) followers")
                .font(.subheadline)
            if isExpanded {
                Text("Joined recently")
            }
            Button("Toggle") {
                isExpanded.toggle()
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(12)
    }
}
