import os, hashlib, collections, sys

EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.mov', '.mkv', '.webm', '.wav', '.mp3', '.flac', '.pdf', '.psd', '.zip', '.pcraft', '.ecproj', '.designcraft', '.vectorcraft'}
SKIP = {'.git', '.venv', '__pycache__'}
root = '.'
files = []
for r, d, f in os.walk(root):
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


groups = []
for sz, ps in by.items():
    if len(ps) < 2:
        continue
    g = collections.defaultdict(list)
    for p in ps:
        g[h(p)].append(p)
    for hh, ps2 in g.items():
        if len(ps2) > 1:
            groups.append((sz, hh, sorted(ps2)))

# already-hardlinked copies share an inode and cost nothing
wasted = 0
pair = collections.Counter()
for sz, hh, ps in groups:
    inodes = {os.stat(p).st_ino for p in ps}
    wasted += sz * (len(inodes) - 1)
    tops = tuple(sorted({'/'.join(p.split('/')[1:3]) for p in ps}))
    pair[tops] += sz * (len(inodes) - 1)

print('files', len(files), 'dup groups', len(groups), 'wasted GB %.2f' % (wasted / 1e9))
for k, v in pair.most_common(25):
    print('%7.0f MB  %s' % (v / 1e6, ' <-> '.join(k)))
