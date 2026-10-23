// LX fork modification: native LightXtreme wire format, 2026-10-24.
import Foundation
import CryptoKit
import CommonCrypto

nonisolated enum LXWire {
    static func authentication(password: String, milliseconds: UInt64) throws -> Data {
        guard password.utf8.count == 32 else { throw failure("LX password must be 32 hex characters") }
        var raw = Data()
        var index = password.startIndex
        for _ in 0..<16 {
            let end = password.index(index, offsetBy: 2)
            guard let b = UInt8(password[index..<end], radix: 16) else { throw failure("Invalid LX hexadecimal password") }
            raw.append(b); index = end
        }
        let mask = [milliseconds &* 10 &+ 3, milliseconds].flatMap { n in
            (0..<8).reversed().map { UInt8(truncatingIfNeeded: n >> ($0 * 8)) }
        }
        return raw + Data(zip(raw, mask).map { $0 ^ $1 })
    }
    static func failure(_ detail: String) -> Error {
        AnywhereError.proxy(.anyTLS, .protocolViolation(detail: detail))
    }
}

// A stream cipher is owned by one serialized direction, never shared across directions.
nonisolated final class LXCTR {
    private let cryptor: CCCryptorRef
    init(key: String, iv: Data) throws {
        guard iv.count == 16 else { throw LXWire.failure("LX IV length") }
        let derived = Data(SHA256.hash(data: Data(key.utf8)).prefix(16))
        var ref: CCCryptorRef?
        let status = derived.withUnsafeBytes { k in iv.withUnsafeBytes { v in
            CCCryptorCreateWithMode(CCOperation(kCCEncrypt), CCMode(kCCModeCTR), CCAlgorithm(kCCAlgorithmAES), CCPadding(ccNoPadding), v.baseAddress, k.baseAddress, 16, nil, 0, 0, CCModeOptions(kCCModeOptionCTR_BE), &ref)
        } }
        guard status == kCCSuccess, let ref else { throw LXWire.failure("LX CTR initialization failed") }
        cryptor = ref
    }
    deinit { CCCryptorRelease(cryptor) }
    func process(_ data: Data) throws -> Data {
        var output = Data(count: data.count)
        let capacity = data.count
        var moved = 0
        let status = output.withUnsafeMutableBytes { dst in data.withUnsafeBytes { src in
            CCCryptorUpdate(cryptor, src.baseAddress, data.count, dst.baseAddress, capacity, &moved)
        } }
        guard status == kCCSuccess else { throw LXWire.failure("LX CTR processing failed") }
        return output.prefix(moved)
    }
}

