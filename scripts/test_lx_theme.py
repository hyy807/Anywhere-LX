#!/usr/bin/env python3
"""Resource/availability contracts; not a substitute for device UI tests."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'Anywhere/Assets.xcassets'

class ThemeContracts(unittest.TestCase):
    def test_theme_colors_have_distinct_light_and_dark_variants(self):
        for name in ('HomeBackgroundStart', 'HomeBackgroundEnd', 'StatCardBackground', 'AccentColor'):
            with self.subTest(name=name):
                data = json.loads((ASSETS / (name + '.colorset') / 'Contents.json').read_text())
                colors = data['colors']
                light = next(c['color'] for c in colors if not c.get('appearances'))
                dark = next(c['color'] for c in colors if {'appearance': 'luminosity', 'value': 'dark'} in c.get('appearances', []))
                self.assertNotEqual(light, dark)

    def test_all_declared_lx_icons_have_previews(self):
        for name in ('LXIcon', 'LXIcon-Classic', 'LXIcon-Muted'):
            for suffix, key in (('.appiconset', 'images'), ('-Sample.imageset', 'images')):
                folder = ASSETS / (name + suffix)
                data = json.loads((folder / 'Contents.json').read_text())
                for image in data[key]:
                    self.assertTrue((folder / image['filename']).is_file())

    def test_configure_preserves_adaptive_resources_and_is_idempotent(self):
        with tempfile.TemporaryDirectory(prefix='lx-theme-') as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            for name in ('configure_lx.py', 'generate_lx_assets.py'):
                shutil.copy2(ROOT / 'scripts' / name, root / 'scripts' / name)
            (root / 'Anywhere.xcodeproj').mkdir()
            shutil.copy2(ROOT / 'Anywhere.xcodeproj/project.pbxproj', root / 'Anywhere.xcodeproj/project.pbxproj')
            for name in ('Anywhere', 'Anywhere Network Extension'):
                (root / name).mkdir()
                shutil.copy2(ROOT / name / 'Info.plist', root / name / 'Info.plist')
            for _ in range(2):
                subprocess.run([sys.executable, 'scripts/configure_lx.py'], cwd=root, check=True, capture_output=True)
                project = (root / 'Anywhere.xcodeproj/project.pbxproj').read_text()
                self.assertIn('LXIcon-Classic LXIcon-Muted', project)
                for file in ASSETS.rglob('*'):
                    if file.is_file():
                        self.assertEqual(file.read_bytes(), (root / file.relative_to(ROOT)).read_bytes())

    def test_theme_editor_is_available_without_store_membership(self):
        source = (ROOT / 'Anywhere/Views/Pages/Personalization/CustomizeThemeView.swift').read_text()
        self.assertNotIn('.disabled(!voyagerStore.isMember)', source)
        self.assertNotIn('VoyagerNotice(', source)

if __name__ == '__main__':
    unittest.main()
