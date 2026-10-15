import SwiftData
import SwiftUI

// Swift 6 language mode, deployment target iOS 27. Version 1.0 shipped with this model.

@Model
final class Entry {
    var remoteID: String
    var title: String
    var amountCents: Int
    var bookedAt: Date

    init(remoteID: String, title: String, amountCents: Int, bookedAt: Date) {
        self.remoteID = remoteID
        self.title = title
        self.amountCents = amountCents
        self.bookedAt = bookedAt
    }
}

@main
struct TallyApp: App {
    var body: some Scene {
        WindowGroup { EntryList() }
            .modelContainer(for: Entry.self)
    }
}

struct EntryList: View {
    @Query(sort: \Entry.bookedAt, order: .reverse) private var entries: [Entry]

    var body: some View {
        List(entries) { entry in
            LabeledContent(entry.title, value: entry.amountCents, format: .number)
        }
    }
}
