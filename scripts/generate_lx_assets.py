#!/usr/bin/env python3
"""Generate original LX resources, never proprietary upstream brand assets.

Upstream main does not publish its asset catalogs. These light/dark defaults
are LX replacements, not a claim of pixel-identical upstream colors.
"""
from pathlib import Path
import json
from struct import pack
import zlib

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'Anywhere/Assets.xcassets'
INFO = {'author': 'LX Native', 'version': 1}


def manifest(folder, data):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'Contents.json').write_text(json.dumps(dict(data, info=INFO), indent=2) + '\n')


def color(hex_value: str, alpha: float = 1):
    return {'color-space': 'srgb', 'components': dict(zip(('red', 'green', 'blue', 'alpha'),
            [*(f'{int(hex_value[i:i+2], 16)/255:.6f}' for i in (0, 2, 4)), str(alpha)]))}


def generate():
    manifest(ASSETS, {})
    for name, light, dark, alpha in (
        ('HomeBackgroundStart', 'DCEEFF', '101F38', 1),
        ('HomeBackgroundEnd', 'F5F7FC', '1F475F', 1),
        ('StatCardBackground', 'FFFFFF', '263344', 0.88),
        ('AccentColor', '146FC0', '72C7FF', 1),
    ):
        manifest(ASSETS / (name + '.colorset'), {'colors': [
            {'idiom': 'universal', 'color': color(light, alpha)},
            {'idiom': 'universal', 'appearances': [{'appearance': 'luminosity', 'value': 'dark'}],
             'color': color(dark, alpha)},
        ]})
    def chunk(t, b):
        return pack('>I', len(b)) + t + b + pack('>I', zlib.crc32(t+b) & 0xffffffff)
    for name, background, foreground in (
        ('LXIcon', (25, 90, 150), (220, 245, 255)),
        ('LXIcon-Classic', (28, 42, 88), (255, 217, 128)),
        ('LXIcon-Muted', (64, 74, 84), (220, 228, 236)),
    ):
        # Original geometric L/X monogram; opaque 1024px App Store icon.
        rows = []
        for y in range(1024):
            row = bytearray(b'\0')
            for x in range(1024):
                mark = (220 < x < 300 and 240 < y < 780 or
                        220 < x < 480 and 700 < y < 780 or
                        500 < x < 820 and 240 < y < 780 and
                        (abs(x - (500 + (y-240)*320/540)) < 43 or
                         abs(x - (820 - (y-240)*320/540)) < 43))
                row.extend(foreground if mark else background)
            rows.append(row)
        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', pack('>IIBBBBB', 1024, 1024, 8, 2, 0, 0, 0)) +
               chunk(b'IDAT', zlib.compress(b''.join(rows))) + chunk(b'IEND', b''))
        for suffix in ('.appiconset', '-Sample.imageset'):
            folder = ASSETS / (name + suffix)
            image = {'filename': 'icon.png', 'idiom': 'universal'}
            if suffix == '.appiconset':
                image.update(platform='ios', size='1024x1024')
            manifest(folder, {'images': [image]})
            (folder / 'icon.png').write_bytes(png)
    for name, path in (
        ('lx', 'M5 4h5v16h10v5H5z M17 4l10 21 M27 4L17 25'),
        ('lx.fill', 'M5 4h5v16h10v5H5z M17 4l10 21 M27 4L17 25'),
    ):
        folder = ASSETS / (name + '.imageset')
        manifest(folder, {'images': [{'idiom': 'universal', 'filename': 'symbol.svg'}],
                          'properties': {'preserves-vector-representation': True, 'template-rendering-intent': 'template'}})
        (folder / 'symbol.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><path d="{path}" fill="none" stroke="black" stroke-width="3" stroke-linejoin="round"/></svg>\n')

if __name__ == '__main__':
    generate()
    print('Generated original LX light/dark colors, three icons/previews and navigation symbols')
