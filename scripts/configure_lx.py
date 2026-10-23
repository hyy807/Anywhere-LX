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
for name in ['Anywhere','Anywhere Network Extension']:
    p=Path(name)/'Info.plist'
    d=plistlib.loads(p.read_bytes()); d['CFBundleDisplayName']='LX Native' if name=='Anywhere' else 'LX Tunnel'
    p.write_bytes(plistlib.dumps(d))
    p=Path(name)/(name+'.entitlements')
    d={'com.apple.security.application-groups':['group.org.hyy807.lxnative'],'com.apple.developer.networking.networkextension':['packet-tunnel-provider']}
    p.write_bytes(plistlib.dumps(d))
# The upstream marks are not licensed for redistribution. Supply original icon.
from struct import pack
import zlib
w=h=1024
rows=b''.join(b'\0'+b''.join(bytes((25,90,150,255)) if not (240<x<780 and 460<y<560 or 240<x<340 and 240<y<780) else bytes((220,245,255,255)) for x in range(w)) for y in range(h))
def chunk(t,b): return pack('>I',len(b))+t+b+pack('>I',zlib.crc32(t+b)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
icon=Path('Anywhere/Assets.xcassets/LXIcon.appiconset');icon.mkdir(parents=True,exist_ok=True)
(icon/'icon.png').write_bytes(png)
(icon/'Contents.json').write_text(json.dumps({'images':[{'filename':'icon.png','idiom':'universal','platform':'ios','size':'1024x1024'}],'info':{'author':'LX Native','version':1}}))
print('Configured LX Native, no team, local-only, iOS 18+, app + NE only')
