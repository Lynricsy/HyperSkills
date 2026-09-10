import Foundation
import Observation

@Observable
final class FeedModel {
    var stories: [Story] = []
    var errorMessage: String?
}

struct Story: Identifiable {
    let id: Int
    let title: String
}

actor StoryCache {
    private var cached: [Int: Story] = [:]

    func story(for id: Int) async throws -> Story {
        if cached[id] == nil {
            cached[id] = try await download(id)
        }

        return cached[id]!
    }

    private func download(_ id: Int) async throws -> Story {
        let url = URL(string: "https://example.com/story/\(id)")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(Story.self, from: data)
    }
}

final class FeedLoader: @unchecked Sendable {
    let model: FeedModel
    let cache = StoryCache()
    var inFlight = 0

    init(model: FeedModel) {
        self.model = model
    }

    func loadAll(ids: [Int]) {
        for id in ids {
            Task.detached {
                let story = try await self.cache.story(for: id)
                DispatchQueue.main.async {
                    self.model.stories.append(story)
                }
            }
        }
    }

    func refresh() {
        Task {
            try await Task.sleep(nanoseconds: 500_000_000)
            try await reload()
        }
    }

    private func reload() async throws {}
}
