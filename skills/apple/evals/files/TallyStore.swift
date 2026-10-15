import SwiftData
import SwiftUI

// Build settings (Tally.xcconfig): SWIFT_VERSION = 6, SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor,
// SWIFT_APPROACHABLE_CONCURRENCY = YES. Deployment target iOS 27.
// Tally.entitlements carries the iCloud container because LeaderboardService talks to the
// public CloudKit database directly with CKContainer. The SwiftData store itself is
// meant to stay on this device.

enum EntryStatus: String, Codable, CaseIterable {
    case pending
    case cleared
    case void
}

@Model
final class Entry {
    @Attribute(.unique) var remoteID: String
    var title: String
    var amountCents: Int
    var status: EntryStatus
    var bookedAt: Date

    init(remoteID: String, title: String, amountCents: Int, status: EntryStatus, bookedAt: Date) {
        self.remoteID = remoteID
        self.title = title
        self.amountCents = amountCents
        self.status = status
        self.bookedAt = bookedAt
    }
}

struct EntryDTO: Codable {
    let id: String
    let title: String
    let amountCents: Int
    let status: EntryStatus
    let bookedAt: Date
}

enum TallyStore {
    static func makeContainer() throws -> ModelContainer {
        let schema = Schema([Entry.self])
        let configuration = ModelConfiguration(schema: schema)
        return try ModelContainer(for: schema, configurations: configuration)
    }
}

@main
struct TallyApp: App {
    let container: ModelContainer

    init() {
        do { container = try TallyStore.makeContainer() }
        catch { fatalError("Store failed: \(error)") }
    }

    var body: some Scene {
        WindowGroup { EntryList() }
            .modelContainer(container)
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
