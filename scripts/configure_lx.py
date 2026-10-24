#!/usr/bin/env python3
"""Reproducible non-signing branding and project configuration."""
from pathlib import Path
import plistlib, re, json
p=Path('Anywhere.xcodeproj/project.pbxproj')
s=p.read_text().replace('com.argsment.Anywhere','org.hyy807.lxnative')
s=re.sub(r'DEVELOPMENT_TEAM = [^;]*;', 'DEVELOPMENT_TEAM = "";', s)
s=s.replace('ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;', 'ASSETCATALOG_COMPILER_APPICON_NAME = LXIcon;')
s=re.sub(r'ASSETCATALOG_COMPILER_ALTERNATE_APPICON_NAMES = [^;]*;', 'ASSETCATALOG_COMPILER_ALTERNATE_APPICON_NAMES = "";', s)
p.write_text(s)
from generate_lx_assets import generate
# Keep checked-in adaptive resources and build-time regeneration identical.
generate()
s=s.replace('ASSETCATALOG_COMPILER_ALTERNATE_APPICON_NAMES = "";', 'ASSETCATALOG_COMPILER_ALTERNATE_APPICON_NAMES = "LXIcon-Classic LXIcon-Muted";')
p.write_text(s)
for name in ['Anywhere','Anywhere Network Extension']:
    p=Path(name)/'Info.plist'
    d=plistlib.loads(p.read_bytes()); d['CFBundleDisplayName']='LX Native' if name=='Anywhere' else 'LX Tunnel'
    p.write_bytes(plistlib.dumps(d))
    p=Path(name)/(name+'.entitlements')
    d={'com.apple.security.application-groups':['group.org.hyy807.lxnative'],'com.apple.developer.networking.networkextension':['packet-tunnel-provider']}
    p.write_bytes(plistlib.dumps(d))
print('Configured LX Native, no team, local-only, iOS 18+, app + NE only')
