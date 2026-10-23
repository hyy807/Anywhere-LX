#!/usr/bin/env python3
"""Source-contract checks; not a substitute for executed Apple tests."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
wire = root / 'Shared/Networking/Protocols/AnyTLS/LXCrypto.swift'
assert wire.exists(), 'Missing native LX wire implementation'
s = wire.read_text()
assert 'milliseconds &* 10 &+ 3' in s
assert 'kCCModeOptionCTR_BE' in s
p = (root / 'Shared/Networking/Protocols/AnyTLS/ProxyClient+AnyTLS.swift').read_text()
assert 'LXTransport.connect' in p
assert 'tunnel != nil || anytls.lxAuth' in p
print('LX source contracts passed (not device validation)')
