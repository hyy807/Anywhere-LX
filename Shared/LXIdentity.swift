// LX fork: resolve the identifiers actually granted by the re-signer.
import Foundation

nonisolated enum LXIdentity {
    static var hostBundle: Bundle {
        if Bundle.main.bundleURL.pathExtension == "appex" {
            return Bundle(url: Bundle.main.bundleURL.deletingLastPathComponent().deletingLastPathComponent()) ?? .main
        }
        return .main
    }
    static var bundle: String { hostBundle.bundleIdentifier ?? "org.hyy807.lxnative" }
    static var extensionIdentifier: String {
        let plugins = hostBundle.bundleURL.appendingPathComponent("PlugIns")
        let entries = (try? FileManager.default.contentsOfDirectory(at: plugins, includingPropertiesForKeys: nil)) ?? []
        for entry in entries {
            guard let b = Bundle(url: entry), let ext = b.infoDictionary?["NSExtension"] as? [String: Any],
                  ext["NSExtensionPointIdentifier"] as? String == "com.apple.networkextension.packet-tunnel" else { continue }
            if let id = b.bundleIdentifier { return id }
        }
        return bundle + ".Network-Extension"
    }
    static let appGroup: String = {
        let own = groups(Bundle.main)
        let host = groups(hostBundle)
        let plugins = hostBundle.bundleURL.appendingPathComponent("PlugIns")
        let entries = (try? FileManager.default.contentsOfDirectory(at: plugins, includingPropertiesForKeys: nil)) ?? []
        let provider = entries.compactMap { Bundle(url: $0) }.first { $0.bundleIdentifier == extensionIdentifier }
        let other = provider.map(groups) ?? host
        let common = Set(host).intersection(other).intersection(own)
        let preferred = "group." + bundle
        let ordered = common.sorted { a, b in a == preferred ? true : b == preferred ? false : a < b }
        if let granted = ordered.first(where: { FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: $0) != nil }) { return granted }
        // Keep the same path contract in both processes; never substitute process tmp.
        return preferred
    }()
    private static func groups(_ bundle: Bundle) -> [String] {
        if let path = bundle.executablePath, let data = try? Data(contentsOf: URL(fileURLWithPath: path), options: .mappedIfSafe),
           let ent = entitlements(data), let groups = ent["com.apple.security.application-groups"] as? [String] { return groups }
        let profile = bundle.bundleURL.appendingPathComponent("embedded.mobileprovision")
        if let data = try? Data(contentsOf: profile),
           let start = data.range(of: Data("<?xml".utf8)), let end = data.range(of: Data("</plist>".utf8)), start.lowerBound < end.upperBound,
           let p = try? PropertyListSerialization.propertyList(from: data[start.lowerBound..<end.upperBound], format: nil) as? [String: Any],
           let ent = p["Entitlements"] as? [String: Any] { return ent["com.apple.security.application-groups"] as? [String] ?? [] }
        return []
    }
    static func entitlements(_ data: Data) -> [String: Any]? {
        func u32(_ offset: Int, be: Bool = false) -> UInt32? {
            guard offset >= 0, offset <= data.count - 4 else { return nil }
            let n = data.withUnsafeBytes { $0.loadUnaligned(fromByteOffset: offset, as: UInt32.self) }
            return be ? UInt32(bigEndian: n) : UInt32(littleEndian: n)
        }
        var slice = 0
        if let magic = u32(0, be: true), magic == 0xcafebabe || magic == 0xcafebabf {
            if magic == 0xcafebabf {
                guard data.count >= 24 else { return nil }
                let offset = data.withUnsafeBytes { UInt64(bigEndian: $0.loadUnaligned(fromByteOffset: 16, as: UInt64.self)) }
                guard offset < UInt64(data.count) else { return nil }; slice = Int(offset)
            } else { guard let offset = u32(16, be: true) else { return nil }; slice = Int(offset) }
        }
        guard u32(slice) == 0xfeedfacf, let count = u32(slice + 16), count < 65536 else { return nil }
        var cursor = slice + 32
        for _ in 0..<count {
            guard let cmd = u32(cursor), let size = u32(cursor + 4), size >= 8, Int(size) <= data.count - cursor else { return nil }
            if cmd == 0x1d, let off = u32(cursor + 8) {
                let blob = slice + Int(off)
                guard u32(blob, be: true) == 0xfade0cc0, let entries = u32(blob + 8, be: true), entries < 65536 else { return nil }
                for i in 0..<Int(entries) {
                    let p = blob + 12 + i * 8
                    guard let type = u32(p, be: true), let offset = u32(p + 4, be: true) else { return nil }
                    if type == 5 {
                        let entry = blob + Int(offset)
                        guard let len = u32(entry + 4, be: true), len >= 8, entry >= 0, entry <= data.count - Int(len) else { return nil }
                        return (try? PropertyListSerialization.propertyList(from: data[(entry + 8)..<(entry + Int(len))], format: nil)) as? [String: Any]
                    }
                }
                return nil
            }
            cursor += Int(size)
        }
        return nil
    }
}
