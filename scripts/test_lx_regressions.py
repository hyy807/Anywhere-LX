#!/usr/bin/env python3
"""Portable regression contracts for the v0.2.2 LX fixes.
These inspect/execute seams only; they do not claim iOS or device validity.
"""
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RegressionContracts(unittest.TestCase):
    def test_localization_and_dynamic_theme_contract(self):
        strings = json.loads((ROOT / 'Shared/Localizable.xcstrings').read_text())['strings']
        expected = {
            'Theme': '主题', 'Personalization': '个性化', 'Reset': '重置',
            'Native networking. Your device. Your settings.': '原生网络。你的设备，你的设置。',
            'Local storage': '本地存储', 'Independent build': '独立构建',
        }
        for key, value in expected.items():
            self.assertEqual(strings[key]['localizations']['zh-Hans']['stringUnit']['value'], value)
        app = (ROOT / 'Anywhere/AnywhereApp.swift').read_text()
        self.assertIn('.environment(settings)', app)
        gradient = (ROOT / 'Anywhere/Views/Components/BackgroundGradient.swift').read_text()
        self.assertIn('homeBackgroundLightStartData', gradient)
        self.assertIn('homeBackgroundDarkStartData', gradient)

    def test_latency_probe_does_not_reuse_closed_warmup_connection(self):
        source = (ROOT / 'Shared/Networking/LatencyTester.swift').read_text()
        self.assertNotIn('establishWarmedConnection', source)
        self.assertEqual(source.count('client.connect(to: Self.latencyHost'), 1)
        self.assertIn('Connection: close', source)

    def test_clash_and_fixture_contracts(self):
        subprocess.run(['python3', 'scripts/test_lx_fixture.py'], cwd=ROOT, check=True)
        parser = (ROOT / 'Shared/Utilities/ClashProxyParser.swift').read_text()
        self.assertIn('withChain([hop])', parser)
        self.assertIn('insecureSkipVerify: getBool(node, key: "skip-cert-verify") ?? false', parser)

if __name__ == '__main__':
    unittest.main()
