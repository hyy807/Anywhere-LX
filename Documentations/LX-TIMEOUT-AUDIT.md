# LX native timeout audit (no app build/release)

## Baselines

- Native repository starting HEAD: `ef931ba2`.
- `git ls-remote upstream HEAD` and `refs/heads/main`: `89905e0e3641bcbd958a66fcb6f027a2bdecec90`, matching local `upstream/main`.
- Working references read: `proxycat-lx/mihomo/transport/anytls/{client,lx}.go`, `transport/lxxhttp/{client,obfs}.go`, adapter outbound AnyTLS layout; also sbvpn transport layout.

## Reproduced and repaired

1. Clash AnyTLS import discarded the entire nested/flat LX transport and `lx-auth`. It now preserves upload path/key, padding and independent download host/port/path; LX transport enables private authentication. Unsupported explicit transports are skipped, not silently downgraded to plain TLS. Stock 32-hex passwords still use standard AnyTLS.
2. Persisted AnyTLS objects containing `lxHTTP` but missing `lxAuth` decoded into private transport with standard authentication. Decode now maintains the same invariant as URL import: private LX transport implies LX authentication.
3. Authentication checked UTF-8 byte count, then indexed Swift Characters in pairs. Thirty ASCII zeros plus `é` has 32 bytes but 31 Characters; real Swift execution crashed with `String index is out of bounds`. Validate ASCII hex before indexing.
4. H2 initial setup returns on server SETTINGS. Response HEADERS therefore normally reach `receiveH2Data`, which silently ignored a rejected status and waited for more frames. A real local TLS/H2 server returning 403 without END_STREAM reproduced this. The production Swift receive function now throws a status-bearing handshake error immediately. 200 plus DATA still delivers `pong`.

## Executed checks

Linux Swift 6.2.1 was downloaded to scratch. Its Ubuntu 22 runtime was isolated in scratch (host is older); no system libc was replaced. Tests execute production function bodies extracted at run time, with small unrelated app type adapters.

```sh
export SWIFT_FRONTEND=/root/.hermes/cache/scratch/lx-swift/swift-6.2.1-RELEASE-ubuntu22.04/usr/bin/swift-frontend
export SWIFT_LIBRARY_PATH=/root/.hermes/cache/scratch/lx-swift/runtime/lib/x86_64-linux-gnu:/root/.hermes/cache/scratch/lx-swift/runtime/usr/lib/x86_64-linux-gnu
python3 scripts/test_lx_import_seam.py
python3 scripts/test_lx_h2_response.py
LX_FIXTURE_STATUS=200 python3 scripts/test_lx_h2_response.py
python3 scripts/test_lx_contract.py
git diff --check
```

- Import seam: 11 PASS assertions; nested/flat layouts, standard compatibility, malformed values, Codable invariant, timestamp change, Unicode rejection.
- Local TLS/H2 fixture: 403 rejected immediately; 200 DATA delivered.
- Reference Go tests (reference only, not native validation): `go test ./transport/anytls ./transport/lxxhttp -count=1 -v` passed 3 tests, including real h2/obfs round trips.
- Additional Apple Testing regressions added to `Anywhere Tests/LXImportTests.swift`; not executed here.

## Confirmed existing behavior / remaining limits

- Native private authentication is generated after physical `dialOut()` for every connection, not in shared client initialization; no stale initialization timestamp bug found in this native path.
- Native LX opens independent upload/download TLS connections, offers only `h2`, uses independent direction cipher actors, and preserves HTTP authority separately from resolved dial IP.
- Offering h2 is not the same as verifying the peer selected h2. Native LX currently does not explicitly check `TLSRecordConnection.negotiatedALPN` before sending H2 prefaces. This remains an identified hardening gap, not a proven user-node cause.
- H2 setup reads lack an LX-specific bounded deadline. Do not introduce an untested structured-concurrency timeout that itself waits forever on a non-cancellation-aware socket; test deadline/cancellation with the actual native transport before altering this.
- Local TLS is Python ssl/h2; actual Swift H2 receive logic is executed on its real frame bytes. This is not an end-to-end test of iOS TLSClient, AES CommonCrypto, split-channel establishment, packet tunnel, or a user's server.
- Plain legacy anytls URLs with only a 32-hex password contain no discriminator between standard AnyTLS and LX. They intentionally remain standard. Such LX nodes require `lx-auth=1` or conversion at a trusted LX-specific import boundary; no blanket heuristic migration was applied.
- No IPA/app build, push, git commit, workflow trigger, or release performed. UI changes in the shared working tree belong to the parallel parent task.
