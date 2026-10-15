// Sources/Billing/Grant.swift — module `Billing`
import Foundation

public struct Grant: Equatable, Decodable, Sendable {
    public let seats: Int
    public let tier: String
}

public enum GrantParser {
    public static func parse(_ json: Data) -> Grant? {
        try? JSONDecoder().decode(Grant.self, from: json)
    }
}
