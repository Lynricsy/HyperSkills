// Tests/BillingTests/GrantTests.swift — test target `BillingTests`
import Foundation
import Testing
import Billing

struct GrantTests {
    @Test func parsesTeamGrant() {
        let json = Data(#"{"seats": 5, "tier": "team"}"#.utf8)
        let grant = GrantParser.parse(json)
        #expect(grant == .init(seats: 5, tier: "team"))
    }
}

/*
 CI log (swift build --build-tests):

 GrantTests.swift:10:26: error: cannot convert value of type 'Grant?' to expected argument type '(any (~Copyable & ~Escapable).Type)?'
 GrantTests.swift:10:32: error: type 'any (~Copyable & ~Escapable).Type' has no member 'init'
*/
