#!/usr/bin/env python3
"""Fixture regression for the supplied Clash profile's compatibility contract.
This is a portable fixture check; it does not claim device connectivity.
"""
from pathlib import Path
import sys
import yaml

root = Path(__file__).resolve().parents[1]
fixture = Path(__import__('os').environ.get(
    'LX_FIXTURE_PATH', '/root/ghbuild/deliver/FlClash-iOS-闪连VPN.yaml'
))
if not fixture.exists():
    raise SystemExit(f'missing fixture: {fixture}; set LX_FIXTURE_PATH to the fixture file')
doc = yaml.safe_load(fixture.read_text())
proxies = doc.get('proxies', [])
groups = {g.get('name'): g for g in doc.get('proxy-groups', []) if isinstance(g, dict)}
assert proxies and groups, 'fixture must contain proxies and proxy-groups'
assert all(p.get('type') in {'anytls', 'vless'} for p in proxies)
anytls = [p for p in proxies if p.get('type') == 'anytls']
assert len(anytls) == 171, len(anytls)
assert all(p.get('skip-cert-verify') is True for p in anytls)
assert all(len(p.get('password', '')) == 32 for p in anytls)
private = [p for p in anytls if p.get('transport', {}).get('type') == 'lx-xhttp']
assert len(private) == 4, len(private)
assert all(p['transport'].get('path') and p['transport'].get('obfs-key') for p in private)
relay = groups['🔗 链式中转']['proxies']
assert relay == ['DIRECT', 'D3'], relay
# Every imported dialer reference must resolve either to a proxy or group.
proxy_names = {p['name'] for p in proxies}
assert all(p['dialer-proxy'] in proxy_names or p['dialer-proxy'] in groups for p in proxies if 'dialer-proxy' in p)
print(f'fixture contract passed: {len(proxies)} proxies, {len(anytls)} AnyTLS, {len(private)} LX-XHTTP, dialer group={relay}')
