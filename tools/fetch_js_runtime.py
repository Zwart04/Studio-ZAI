"""Fetch the pinned small Windows JS runtime needed by yt-dlp EJS."""
import hashlib
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://github.com/quickjs-ng/quickjs/releases/download/v0.17.0/qjs-windows-x86_64.exe'
SHA256 = '2aeabf0092c3262d6b2609824418f7dd7ed1f1df939f73b2b15645230cac0d77'


def main():
    target = ROOT/'vendor/qjs.exe'
    data = urllib.request.urlopen(URL,timeout=60).read()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise RuntimeError('QuickJS checksum mismatch')
    target.write_bytes(data)
    license_text = urllib.request.urlopen('https://raw.githubusercontent.com/quickjs-ng/quickjs/v0.17.0/LICENSE',timeout=30).read()
    (ROOT/'docs/licenses/QUICKJS-NG-LICENSE.txt').write_bytes(license_text)
    print('QuickJS-NG v0.17.0 verified:',len(data),'bytes')


if __name__ == '__main__':
    main()
