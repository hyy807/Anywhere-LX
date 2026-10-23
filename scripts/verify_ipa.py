#!/usr/bin/env python3
"""Verify delivered IPA bytes, never infer success from CI alone."""
import zipfile,plistlib,struct,hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);z=zipfile.ZipFile(p);assert z.testzip() is None
assert not [n for n in z.namelist() if '_CodeSignature' in n or n.endswith('embedded.mobileprovision')]
root=next(n[:-10] for n in z.namelist() if n.endswith('/Info.plist') and n.count('/')==2)
main=plistlib.loads(z.read(root+'Info.plist'))
exts=[n for n in z.namelist() if n.endswith('.appex/Info.plist')];assert len(exts)==1
ext=plistlib.loads(z.read(exts[0])); assert ext['CFBundleIdentifier'].startswith(main['CFBundleIdentifier']+'.')
assert ext['NSExtension']['NSExtensionPointIdentifier']=='com.apple.networkextension.packet-tunnel'
assert main['CFBundleDisplayName']=='LX Native'
report={'file':p.name,'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'zip_crc':'pass','app':main,'extension':ext,'binaries':[]}
for prefix,info in [(root,main),(exts[0][:-10],ext)]:
    d=z.read(prefix+info['CFBundleExecutable']); assert struct.unpack_from('<I',d)[0]==0xfeedfacf
    count=struct.unpack_from('<I',d,16)[0];cursor=32;signature=False
    for _ in range(count):
        cmd,size=struct.unpack_from('<II',d,cursor); assert size>=8
        if cmd==0x1d: signature=True
        cursor+=size
    assert not signature
    for marker in [b'LX invalid obfs sync marker',b'LX password must be 32 hex characters',b'com.apple.security.application-groups']:
        assert marker in d,(prefix,marker)
    report['binaries'].append({'path':prefix+info['CFBundleExecutable'],'bytes':len(d),'native_LX_markers':True,'LC_CODE_SIGNATURE':False})
print(json.dumps(report,indent=2,default=str))
p.with_suffix('.verification.json').write_text(json.dumps(report,indent=2,default=str))
