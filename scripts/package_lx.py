from pathlib import Path
import plistlib, shutil, subprocess
app=Path('delivery/Payload/LXNative.app')
for p in list(app.rglob('_CodeSignature')):
    if p.is_dir(): shutil.rmtree(p)
for p in app.rglob('embedded.mobileprovision'): p.unlink()
for bundle in [app,*app.glob('PlugIns/*.appex')]:
    info=plistlib.loads((bundle/'Info.plist').read_bytes())
    subprocess.run(['codesign','--remove-signature',str(bundle/info['CFBundleExecutable'])],check=False)
    ent={'com.apple.security.application-groups':['group.org.hyy807.lxnative'],'com.apple.developer.networking.networkextension':['packet-tunnel-provider']}
    (Path('delivery')/('App.entitlements.plist' if bundle==app else 'Tunnel.entitlements.plist')).write_bytes(plistlib.dumps(ent))
assert len(list(app.glob('PlugIns/*.appex')))==1
print('Packaged unsigned app + packet tunnel; no profiles or team')
