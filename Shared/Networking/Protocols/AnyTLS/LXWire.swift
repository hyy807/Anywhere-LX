// LX fork native transport, 2026-10-24.
import Foundation

nonisolated struct LXHTTPConfiguration: Codable, Hashable, Sendable {
    var path: String = "/"
    var obfsKey: String = ""
    var download: String = ""
    var downloadPort: UInt16? = nil
    var downloadPath: String = ""
    var paddingMin: Int = 100
    var paddingMax: Int = 1000
}

private actor LXObfsDirection {
    let key: String
    var cipher: LXCTR?
    var header = Data()
    init(key: String) { self.key = key }
    func encode(_ data: Data) throws -> Data {
        if key.isEmpty { return data }
        if let cipher { return try cipher.process(data) }
        var rng = SystemRandomNumberGenerator()
        let iv = Data((0..<16).map { _ in UInt8.random(in: 0...255, using: &rng) })
        let c = try LXCTR(key: key, iv: iv)
        cipher = c
        return iv + (try c.process(Data(repeating: 0, count: 4) + data))
    }
    func decode(_ data: Data) throws -> Data {
        if key.isEmpty { return data }
        if let cipher { return try cipher.process(data) }
        header.append(data)
        guard header.count >= 20 else { return Data() }
        let c = try LXCTR(key: key, iv: Data(header.prefix(16)))
        let plain = try c.process(Data(header.dropFirst(16)))
        guard plain.prefix(4) == Data(repeating: 0, count: 4) else { throw LXWire.failure("LX invalid obfs sync marker") }
        cipher = c; header.removeAll()
        return Data(plain.dropFirst(4))
    }
}

nonisolated final class LXObfsConnection: ProxyConnection {
    let inner: ProxyConnection
    private let upload: LXObfsDirection
    private let download: LXObfsDirection
    private let sender = SerialSender()
    init(inner: ProxyConnection, key: String) {
        self.inner = inner; upload = LXObfsDirection(key: key); download = LXObfsDirection(key: key)
    }
    var isConnected: Bool { inner.isConnected }
    func sendRaw(_ data: Data) async throws {
        try await sender.run { [self] in try await inner.send(upload.encode(data)) }
    }
    func receiveRaw() async throws -> Data? {
        while let bytes = try await inner.receive() {
            let plain = try await download.decode(bytes)
            if !plain.isEmpty { return plain }
        }
        return nil
    }
    func cancel() { inner.cancel() }
}

nonisolated enum LXTransport {
    static func connect(host: String, port: UInt16, authorityHost: String, tls: TLSConfiguration, options: LXHTTPConfiguration, tunnel: ProxyConnection?) async throws -> ProxyConnection {
        guard tunnel == nil else { throw LXWire.failure("LX split transport cannot reuse one chain tunnel for two TLS connections") }
        let session = UUID().uuidString.lowercased()
        func configuration(host: String, path: String) -> XHTTPConfiguration {
            let normalized = "/" + path.split(separator: "/").joined(separator: "/") + (path == "/" ? "" : "/")
            return XHTTPConfiguration(host: host, path: normalized, mode: .streamUp, xPaddingBytesFrom: max(0, min(options.paddingMin, 8192)), xPaddingBytesTo: max(0, min(max(options.paddingMin, options.paddingMax), 8192)))
        }
        let dlHost = options.download.isEmpty ? host : options.download
        let dlPort = options.downloadPort ?? port
        let dlPath = options.downloadPath.isEmpty ? options.path : options.downloadPath
        let uploadTLS = TLSConfiguration(serverName: tls.serverName, alpn: ["h2"], minVersion: tls.minVersion, maxVersion: tls.maxVersion, echEnabled: tls.echEnabled, echConfig: tls.echConfig, fingerprint: tls.fingerprint, insecureSkipVerify: tls.insecureSkipVerify)
        let downloadTLS = TLSConfiguration(serverName: options.download.isEmpty ? tls.serverName : dlHost, alpn: ["h2"], minVersion: tls.minVersion, maxVersion: tls.maxVersion, echEnabled: tls.echEnabled, echConfig: tls.echConfig, fingerprint: tls.fingerprint, insecureSkipVerify: tls.insecureSkipVerify)
        let u = TLSClient(configuration: uploadTLS)
        let upload: TLSRecordConnection
        if let tunnel { upload = try await u.connect(overTunnel: tunnel) }
        else { upload = try await u.connect(host: host, port: port) }
        func authority(_ name: String, _ port: UInt16) -> String {
            let bracketed = name.contains(":") ? "[\(name)]" : name
            return port == 443 ? bracketed : "\(bracketed):\(port)"
        }
        let up = XHTTPConnection(download: TLSByteTransport(upload), configuration: configuration(host: authority(authorityHost, port), path: options.path), mode: .streamUp, sessionId: session, useHTTP2: true)
        up.configureRole(.uploadOnly)
        do {
            // Upload SETTINGS completes before any response body is required.
            try await up.performSetup()
            let dl = try await TLSClient(configuration: downloadTLS).connect(host: dlHost, port: dlPort)
            let down = XHTTPConnection(download: TLSByteTransport(dl), configuration: configuration(host: authority(options.download.isEmpty ? authorityHost : dlHost, dlPort), path: dlPath), mode: .streamUp, sessionId: session, useHTTP2: true)
            down.configureRole(.downloadOnly)
            do {
                try await down.performSetup()
                down.attachUploadChannel(up)
                return LXObfsConnection(inner: XHTTPProxyConnection(xhttpConnection: down), key: options.obfsKey)
            } catch { down.cancel(); throw error }
        } catch { up.cancel(); throw error }
    }
}
