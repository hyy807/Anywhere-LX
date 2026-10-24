#!/usr/bin/env python3
"""Convert a trusted LX-provider Clash file; never infer LX from password shape.
Requires PyYAML. Output contains credentials: keep it outside the repository.
Plain provider nodes use LX auth over TLS; only explicit LX-XHTTP nodes get XHTTP.
"""
import argparse
import os
from pathlib import Path
import re
from urllib.parse import quote, urlencode
import yaml


def convert(node):
    if node.get('type') != 'anytls':
        return None
    password = str(node['password'])
    if not re.fullmatch(r'[0-9a-fA-F]{32}', password):
        raise ValueError('Invalid LX password; expected 32 ASCII hex characters')
    host = str(node['server'])
    if ':' in host:
        host = '[' + host + ']'
    port = int(node['port'])
    if not 1 <= port <= 65535:
        raise ValueError('Invalid server port')
    query = {'lx-auth': '1', 'sni': node.get('sni') or node.get('servername') or node['server']}
    if node.get('skip-cert-verify'):
        query['allowInsecure'] = '1'
    transport = node.get('transport')
    if transport:
        if not isinstance(transport, dict) or transport.get('type') not in ('lx-xhttp', 'xhttp', 'lightxtreme', '闪电旋风劈'):
            raise ValueError('Unsupported explicit transport')
        query.update({'transport': 'lx-xhttp', 'path': transport.get('path', '/'), 'obfs-key': transport.get('obfs-key', '')})
        download = transport.get('download') or {}
        if download:
            query['download'] = download['server']
            if 'port' in download:
                if not 1 <= int(download['port']) <= 65535:
                    raise ValueError('Invalid download port')
                query['download-port'] = str(download['port'])
            query['download-path'] = download.get('path', '')
        for key in ('padding-min', 'padding-max'):
            if key in transport:
                query[key] = str(transport[key])
    return f'anytls://{quote(password, safe="")}@{host}:{port}?{urlencode(query, quote_via=quote)}#{quote(str(node.get("name", "LX")), safe="")}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--trusted-lx-provider', action='store_true', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.output.resolve().is_relative_to(root):
        parser.error('Credential output must be outside the repository')
    nodes = yaml.safe_load(args.source.read_text())['proxies']
    links = [link for node in nodes if (link := convert(node))]
    if not links:
        parser.error('No AnyTLS nodes found')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w') as stream:
        os.chmod(args.output, 0o600)
        stream.write('\n'.join(links) + '\n')
    print(f'Converted {len(links)} trusted LX nodes; output is private (0600)')


if __name__ == '__main__':
    main()
