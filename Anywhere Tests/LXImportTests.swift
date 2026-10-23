// LX fork regressions: real parser, export, Codable and stream obfuscation.
import Testing
import Foundation
@testable import Anywhere

struct LXImportTests {
    @Test func explicitOptInAndRoundTrip() throws {
        let base = "anytls://00112233445566778899aabbccddeeff@example.invalid:443"
        let plain = try ProxyConfiguration.parse(url: base)
        #expect(plain.anytls?.lxAuth == false)
        #expect(plain.anytls?.lxHTTP == nil)
        let privateTLS = try ProxyConfiguration.parse(url: base + "?lx-auth=1")
        #expect(privateTLS.anytls?.lxAuth == true)
        let split = try ProxyConfiguration.parse(url: base + "?transport=lx-xhttp&path=%2Fup&obfs-key=test%26key&download=dl.example.invalid&download-port=8443&download-path=%2Fdown&padding-min=12&padding-max=24")
        #expect(split.anytls?.lxHTTP?.obfsKey == "test&key")
        let exported = try ProxyConfiguration.parse(url: split.toURLString())
        #expect(exported.anytls == split.anytls)
        let stored = try JSONDecoder().decode(ProxyConfiguration.self, from: JSONEncoder().encode(split))
        #expect(stored.anytls == split.anytls)
    }
    @Test func rejectsMalformedPrivatePassword() {
        #expect(throws: (any Error).self) {
            try ProxyConfiguration.parse(url: "anytls://not-hex@example.invalid:443?lx-auth=1")
        }
    }
}
