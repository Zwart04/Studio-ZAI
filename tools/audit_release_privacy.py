"""Check Git history and release archives without printing secret values.

This detects common token formats and private filenames, not every possible
secret. Run before publishing; findings are paths only, never matching values.
"""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|AIza[A-Za-z0-9_-]{35}|sk-(?:proj-|ant-|or-v1-)?[A-Za-z0-9_-]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


def private_name(name):
    name = Path(name).name.lower()
    return ((name == '.env' or name.startswith('.env.') and name not in {'.env.example', '.env.template'})
            or name in {'credentials.json', 'cookies.txt', 'settings.local.json', 'key.properties'}
            or name.endswith(('.keystore', '.p12', '.pfx')))


def scan(archives=()):
    findings = set()
    public_fingerprints = json.loads((ROOT / 'tools/public_dependency_tokens.json').read_text())
    excluded_public = 0
    tracked = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
    for name in filter(None, tracked):
        path = ROOT / name
        if private_name(name): findings.add('working:' + name)
        if path.is_file() and path.stat().st_size < 2 * 1024 * 1024 and TOKENS.search(path.read_bytes()): findings.add('working:' + name)
    objects = subprocess.check_output(['git', 'rev-list', '--objects', '--all'], cwd=ROOT).decode().splitlines()
    identities = [row.split(' ', 1) for row in objects]
    proc = subprocess.Popen(['git', 'cat-file', '--batch-check'], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    sizes, _ = proc.communicate(('\n'.join(row[0] for row in identities) + '\n').encode())
    selected = []
    for row, info in zip(identities, sizes.decode().splitlines()):
        fields = info.split()
        if len(row) < 2: continue
        if private_name(row[1]): findings.add('history:' + row[1])
        if len(fields) == 3 and fields[1] == 'blob' and int(fields[2]) < 2 * 1024 * 1024: selected.append(row)
    proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    raw, _ = proc.communicate(('\n'.join(row[0] for row in selected) + '\n').encode())
    position = 0
    for identity in selected:
        header_end = raw.index(b'\n', position)
        size = int(raw[position:header_end].split()[-1])
        blob = raw[header_end + 1:header_end + 1 + size]
        if TOKENS.search(blob): findings.add('history:' + identity[1])
        position = header_end + 1 + size + 1
    for archive in archives:
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                if private_name(entry.filename): findings.add(Path(archive).name + ':' + entry.filename)
                if not entry.is_dir() and entry.file_size < 32 * 1024 * 1024:
                    matches = TOKENS.findall(bundle.read(entry))
                    verified = public_fingerprints.get(Path(entry.filename).name, {}).get('sha256', []) if entry.filename.startswith('_internal/yt_dlp/extractor/') else []
                    excluded_public += sum(hashlib.sha256(value).hexdigest() in verified for value in matches)
                    if any(hashlib.sha256(value).hexdigest() not in verified for value in matches):
                        findings.add(Path(archive).name + ':' + entry.filename)
            if bundle.testzip(): raise RuntimeError('Archive integrity failed')
    return {'tracked_files': len(list(filter(None, tracked))), 'history_blobs': len(selected), 'archives': len(archives), 'verified_public_dependency_tokens': excluded_public, 'findings': sorted(findings)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archives', nargs='*')
    args = parser.parse_args()
    report = scan(args.archives)
    print(json.dumps(report, indent=2))
    raise SystemExit(bool(report['findings']))
