# LX Native — independent native Swift fork

This fork adapts the GPLv3 source of NodePassProject/Anywhere. It is not an official release or endorsed by NodePassProject. Distributed app name/icon are replaced with **LX Native**. All upstream copyright/license notices remain. Fork modifications started 2026-10-24; see Git history for changed files.

## Import

Paste AnyTLS sharing links in Add Proxy (or import a URL-list subscription).
Stock `anytls://` remains standard SHA256 authentication even for 32-hex passwords.
For LightXtreme/闪连 plain TLS, add `lx-auth=1`:

```text
anytls://00112233445566778899aabbccddeeff@example.invalid:443?lx-auth=1&sni=example.invalid#LX-plain-example
```

For the private split H2 carrier:

```text
anytls://00112233445566778899aabbccddeeff@example.invalid:443?transport=lx-xhttp&path=%2Fupload&obfs-key=example-only&download=download.example.invalid&download-port=443&download-path=%2Fdownload&padding-min=100&padding-max=1000#LX-H2-example
```

These are **synthetic, nonworking examples**, not real nodes. Percent-encode query values. Parameters survive app storage and link export. Both legs share a UUID; upstream POST `application/grpc`, downstream GET; Referer padding; AES-128-CTR uses SHA256(key)[:16], independent IVs, encrypted zero marker. Inner AnyTLS does not add TLS again. Plain and lx-xhttp private auth uses `raw16 || (BE64(n*10+3)||BE64(n) xor raw16)` at session creation, not a cached timestamp.

This fork supplies URL imports, not a claim of complete Clash YAML compatibility. The upstream includes a limited Clash subscription parser, but private LX fields are supported by the explicit links above / this app's Codable configuration, not arbitrary Clash YAML. Do not import a Clash policy profile and expect groups/rules to migrate.

## Self-sign build

Workflow `.github/workflows/lx-ios.yml` builds native Swift/C for iPhone/iPad arm64, minimum iOS 18. No Go/mihomo replacement, no team/profile embedded, only host + packet tunnel. Re-sign both bundles. Runtime uses the installed bundle IDs and intersects signed App Groups; shared IPC stays in the App Group. No per-device build is needed.

Cloud sync is disabled; local SwiftData storage stays enabled. File imports acquire coordinated bytes under security scope. Proxy-row latency uses a sibling Button and the native proxy data channel, not ICMP or an unproxied TCP ping.

## Verification boundaries

CI executes production Swift auth/CTR known-answer and split-stream tests, then Apple iOS compilation. `scripts/test_lx_contract.py` is explicitly a source-contract check, not a network/device test. ZIP integrity, bundle structure, protocol markers, signing residue and hashes are checked separately before release. No physical-device installation, NE startup, Files-provider hit testing or real-node interoperability is established merely by a green build.
