import Foundation
@main struct LXWireTests {
    static func main() throws {
        func hex(_ data: Data) -> String { data.map { String(format: "%02x", $0) }.joined() }
        let auth = try LXWire.authentication(password: "00112233445566778899aabbccddeeff", milliseconds: 1700000000123)
        precondition(hex(auth) == "00112233445566778899aabbccddeeff00112d455aa372a68899ab3003388684")
        for invalid in ["", "short", String(repeating: "z", count: 32)] {
            do { _ = try LXWire.authentication(password: invalid, milliseconds: 0); fatalError("Invalid password accepted") } catch {}
        }
        let iv = Data(0..<16)
        let c = try LXCTR(key: "test-key", iv: iv)
        let first = try c.process(Data(repeating: 0, count: 4))
        let second = try c.process(Data("hello LX".utf8))
        precondition(hex(first + second) == "a29d376c1af5452fd8d4597b")
        let d = try LXCTR(key: "test-key", iv: iv)
        let plain = try d.process(first + second)
        precondition(plain == Data(repeating: 0, count: 4) + Data("hello LX".utf8))
        print("PASS: auth known answer, malformed input, AES-128-CTR known answer, split-stream continuity, decrypt")
    }
}
