#!/usr/bin/env python3
"""Execute the production AnyTLS Clash parsing seam with Swift + real libyaml.
Not a whole-app or Apple networking test. SWIFT_FRONTEND may select Linux Swift.
"""
from pathlib import Path
import os, subprocess, tempfile
ROOT = Path(__file__).resolve().parents[1]
def declaration(text, marker):
    start = text.index(marker)
    brace = text.index('{', start)
    depth = 1
    end = brace + 1
    while depth:
        if text[end] == '{': depth += 1
        elif text[end] == '}': depth -= 1
        end += 1
    return text[start:end]
parser = (ROOT / 'Shared/Utilities/ClashProxyParser.swift').read_text()
helpers = ['private static func getString(', 'private static func getInt(', 'private static func getBool(', 'private static func getStringSequence(', 'private static func parseBasics(', 'private static func parseAnyTLSProxy(']
# Configuration and parser bodies are read directly, not reimplemented in Python.
source = '''import Foundation
struct TLSConfiguration: Hashable, Codable, Sendable {
 var serverName: String; var alpn: [String]?; var echEnabled: Bool; var echConfig: String?; var fingerprint: String
 init(serverName: String, alpn: [String]? = nil, echEnabled: Bool = false, echConfig: String? = nil, fingerprint: String = "default", insecureSkipVerify: Bool = false) { self.serverName=serverName; self.alpn=alpn; self.echEnabled=echEnabled; self.echConfig=echConfig; self.fingerprint=fingerprint }
}
enum GenericSecurityLayer: Hashable, Codable, Sendable { case tls(TLSConfiguration); var tlsConfiguration: TLSConfiguration? { if case .tls(let t)=self {return t}; return nil } }
enum Outbound { case anytls(AnyTLSConfiguration) }
struct ProxyConfiguration { var name: String; var serverAddress: String; var serverPort: UInt16; var outbound: Outbound; var anytls: AnyTLSConfiguration? { if case .anytls(let a)=outbound {return a}; return nil } }
struct TestError: Error {}
enum AnywhereError { enum Kind { case yaml(detail: String) }; static func parse(_ x: Kind) -> TestError {TestError()} }
'''
source += (ROOT/'Shared/Utilities/YAML/YAML.swift').read_text()
source += declaration((ROOT/'Shared/Networking/Protocols/AnyTLS/LXWire.swift').read_text(), 'nonisolated struct LXHTTPConfiguration')
source += (ROOT/'Shared/Networking/Protocols/AnyTLS/AnyTLSConfiguration.swift').read_text()
source += declaration((ROOT/'Shared/Networking/Protocols/AnyTLS/LXCrypto.swift').read_text(), '    static func authentication(').replace('throw failure(', 'throw TestFailure(')
source += '''
func TestFailure(_ s: String) -> TestError { TestError() }
enum LXWire { static func authentication(password: String, milliseconds: UInt64) throws -> Data { try SwiftAuthentication(password: password, milliseconds: milliseconds) } }
'''
# Rename the top-level extracted authentication function to avoid recursion.
source = source.replace('    static func authentication(password:', 'func SwiftAuthentication(password:', 1)
source += '\nstruct Parser {\n' + '\n'.join(declaration(parser, m) for m in helpers)
source += '''
 static func parseSNI(_ node: YAML.Node, server: String) -> String { node["sni"].type == .scalar ? node["sni"].scalar : server }
 static func parseFingerprint(_ node: YAML.Node) -> String { "default" }
 static func echSettings(_ node: YAML.Node) -> (enabled: Bool, config: String?) { (false,nil) }
 static func run(_ yaml: String) throws -> ProxyConfiguration? { parseAnyTLSProxy(try YAML.load(yaml)) }
}
let base = "name: fixture\\ntype: anytls\\nserver: example.invalid\\nport: 443\\npassword: 00112233445566778899aabbccddeeff\\n"
func check(_ ok: Bool, _ label: String) { if !ok { print("FAIL: "+label); exit(1) }; print("PASS: "+label) }
let stock = try Parser.run(base)!.anytls!
check(!stock.lxAuth && stock.lxHTTP == nil, "stock 32-hex stays standard")
let nested = try Parser.run(base + "transport:\\n  type: xhttp\\n  path: /up\\n  obfs-key: test-key\\n  padding-min: 12\\n  padding-max: 24\\n  download:\\n    server: dl.invalid\\n    port: 8443\\n    path: /down\\n")!.anytls!
check(nested.lxAuth, "nested private transport enables LX auth")
check(nested.lxHTTP?.obfsKey == "test-key" && nested.lxHTTP?.downloadPort == 8443 && nested.lxHTTP?.downloadPath == "/down", "nested transport retains fields")
let plain = try Parser.run(base + "lx-auth: true\\n")!.anytls!
check(plain.lxAuth && plain.lxHTTP == nil, "explicit plain TLS LX")
let flat = try Parser.run(base + "obfs-key: flat-key\\npath: /flat\\ndownload: dl.invalid\\ndownload-port: 9443\\n")!.anytls!
check(flat.lxAuth && flat.lxHTTP?.downloadPort == 9443, "flat LX transport retains fields")
check(try Parser.run(base + "transport:\\n  type: ws\\n") == nil, "unsupported transport rejected, never silently TLS")
let firstAuth = try LXWire.authentication(password: "00112233445566778899aabbccddeeff", milliseconds: 1700000000123)
let nextAuth = try LXWire.authentication(password: "00112233445566778899aabbccddeeff", milliseconds: 1700000001123)
check(firstAuth != nextAuth && firstAuth.prefix(16) == nextAuth.prefix(16), "private authentication refreshes timestamp")
do { _ = try LXWire.authentication(password: String(repeating: "0", count: 30) + "é", milliseconds: 0); check(false, "Unicode password rejected") } catch { print("PASS: Unicode password rejected safely") }
let splitJSON = try JSONEncoder().encode(nested)
var splitObject = try JSONSerialization.jsonObject(with: splitJSON) as! [String: Any]
splitObject.removeValue(forKey: "lxAuth")
let migrated = try JSONDecoder().decode(AnyTLSConfiguration.self, from: JSONSerialization.data(withJSONObject: splitObject))
check(migrated.lxAuth, "persisted LX transport never downgrades authentication")
let malformed = base.replacingOccurrences(of: "00112233445566778899aabbccddeeff", with: "bad")
check(try Parser.run(malformed + "lx-auth: true\\n") == nil, "malformed LX auth rejected")
check(try Parser.run(base + "transport:\\n  type: xhttp\\n  download:\\n    port: 70000\\n") == nil, "invalid download port rejected")
'''
with tempfile.TemporaryDirectory(prefix='lx-import-', dir=os.environ.get('TMPDIR')) as tmp:
    script = Path(tmp)/'main.swift'; script.write_text(source)
    cmd = [os.environ.get('SWIFT_FRONTEND','swift-frontend'), '-interpret', '-swift-version','6', '-import-objc-header','/usr/include/yaml.h', '-lyaml', str(script)]
    env = os.environ.copy()
    if env.get('SWIFT_LIBRARY_PATH'): env['LD_LIBRARY_PATH'] = env['SWIFT_LIBRARY_PATH']
    raise SystemExit(subprocess.run(cmd, env=env).returncode)
