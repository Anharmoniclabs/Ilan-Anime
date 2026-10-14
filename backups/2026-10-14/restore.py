"""Restore a completed Ilan-Anime Git-object ZIP backup into an existing clone."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
import zlib

def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(data)
    return value.hexdigest()

def install_object(objects, sha, compressed):
    raw = zlib.decompress(compressed)
    if hashlib.sha1(raw).hexdigest() != sha:
        raise RuntimeError('Git object checksum mismatch: ' + sha)
    header, body = raw.split(b'\0', 1)
    kind, size = header.split()
    if kind not in {b'blob', b'tree', b'commit', b'tag'} or len(body) != int(size):
        raise RuntimeError('Invalid Git object: ' + sha)
    target = objects / sha[:2] / sha[2:]
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
        output.write(compressed)
        temporary = Path(output.name)
    temporary.replace(target)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--archives', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    manifest = json.loads((args.archives / 'manifest.json').read_text())
    if not manifest.get('complete') or len(manifest['volumes']) != manifest['expected_volumes']:
        raise RuntimeError('Backup upload is incomplete; download the completed manifest and all volumes first')
    git = ['git', '-C', str(args.repo.resolve())]
    subprocess.run(git + ['cat-file', '-e', manifest['base_commit'] + '^{commit}'], check=True)
    common = Path(subprocess.check_output(git + ['rev-parse', '--git-common-dir'], text=True).strip())
    if not common.is_absolute():
        common = args.repo.resolve() / common
    objects = common / 'objects'
    with tempfile.TemporaryDirectory(prefix='ilan-restore-') as temporary:
        segments = Path(temporary)
        ranges = {}
        for record in manifest['volumes']:
            path = args.archives / record['filename']
            if path.stat().st_size != record['bytes'] or digest(path) != record['sha256']:
                raise RuntimeError('ZIP checksum mismatch: ' + path.name)
            with zipfile.ZipFile(path) as archive:
                for member in archive.infolist():
                    direct = re.fullmatch(r'objects/([0-9a-f]{2})/([0-9a-f]{38})', member.filename)
                    segment = re.fullmatch(r'segments/([0-9a-f]{40})/([0-9]{12})', member.filename)
                    data = archive.read(member)
                    if direct:
                        install_object(objects, direct[1] + direct[2], data)
                    elif segment:
                        sha, offset = segment[1], int(segment[2])
                        part = segments / sha
                        with part.open('r+b' if part.exists() else 'wb') as output:
                            output.seek(offset)
                            output.write(data)
                        ranges.setdefault(sha, []).append((offset, len(data)))
                    else:
                        raise RuntimeError('Unexpected ZIP member: ' + member.filename)
            print('Verified and imported ' + path.name, flush=True)
        for sha, pieces in ranges.items():
            expected = 0
            for offset, size in sorted(pieces):
                if offset != expected:
                    raise RuntimeError('Missing or overlapping object segment: ' + sha)
                expected += size
            install_object(objects, sha, (segments / sha).read_bytes())
    target = manifest['saved_commit']
    subprocess.run(git + ['fsck', '--connectivity-only', '--no-dangling', target], check=True)
    branch = 'restored-local-' + target[:12]
    current = subprocess.run(git + ['rev-parse', '--verify', 'refs/heads/' + branch], capture_output=True, text=True)
    if current.returncode == 0 and current.stdout.strip() != target:
        raise RuntimeError('Restore branch already exists at another commit')
    if current.returncode != 0:
        subprocess.run(git + ['update-ref', 'refs/heads/' + branch, target, '0' * 40], check=True)
    print(f'Restored exact commit {target} to branch {branch}.')
    print(f'To inspect it: git -C {args.repo} switch {branch}')

if __name__ == '__main__':
    main()
