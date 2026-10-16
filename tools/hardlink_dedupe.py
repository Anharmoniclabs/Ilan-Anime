import os, hashlib, collections

EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.mov', '.mkv', '.webm', '.wav', '.mp3', '.flac', '.pdf', '.psd', '.zip', '.pcraft', '.ecproj', '.designcraft', '.vectorcraft'}
SKIP = {'.git', '.venv', '__pycache__'}
files = []
for r, d, f in os.walk('.'):
    d[:] = [x for x in d if x not in SKIP]
    for n in f:
        if os.path.splitext(n)[1].lower() in EXT:
            p = os.path.join(r, n)
            if os.path.isfile(p) and not os.path.islink(p):
                files.append(p)

by = collections.defaultdict(list)
for p in files:
    by[os.path.getsize(p)].append(p)


def h(p):
    s = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            s.update(c)
    return s.hexdigest()


linked = freed = 0
for sz, ps in by.items():
    if len(ps) < 2 or sz == 0:
        continue
    g = collections.defaultdict(list)
    for p in ps:
        g[h(p)].append(p)
    for ps2 in g.values():
        ps2.sort(key=lambda p: (p.startswith('./archive'), len(p), p))
        keep = ps2[0]
        ino = os.stat(keep).st_ino
        for p in ps2[1:]:
            if os.stat(p).st_ino == ino:
                continue
            tmp = p + '.hl-tmp'
            os.link(keep, tmp)
            os.replace(tmp, p)
            linked += 1
            freed += sz
print('relinked', linked, 'files, freed %.2f GB' % (freed / 1e9))
