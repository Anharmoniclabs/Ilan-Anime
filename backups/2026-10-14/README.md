# Ilan-Anime local production backup — 2026-10-14

**Check `manifest.json`: the backup is ready only when `complete` is `true`.**

The numbered ZIPs preserve all four pending local commits, ending at
`a01870d4b0609adb9236d2e9262eac3b23b720dd`. Together with the existing GitHub
history through `e10efd46ea5162d2f3396322b1cd74a1b3b6bc80`, they restore the
exact local project: 39,567 tracked files and symlinks.

ZIPs are grouped into Git history, engine and documentation, shot artwork,
production records and native projects, episode source assets, related
workspaces, and research. The backup includes the archived AnimeMotion and
HeraldsOfTheCemi workspaces. Runtime caches, environments, and ignored process
logs are excluded. Archiving does not change creative approval or imply a
finished animated episode.

These ZIPs contain compressed Git objects, so repeated artwork is stored once
and the original commits can be recovered exactly. They are **not individual
source-code ZIPs**. Most volumes are at most about 24 MiB; larger Git objects
are divided across volumes. Download every ZIP listed in the completed manifest,
plus `manifest.json` and `restore.py`, into the same directory.

```sh
git clone --branch main https://github.com/Anharmoniclabs/Ilan-Anime.git Ilan-Anime-restored
python3 restore.py --repo ./Ilan-Anime-restored
```

The script verifies ZIP SHA-256 checksums, the original Git object hashes, and
history connectivity. It creates `restored-local-a01870d4b060` without changing
main or checking out files. To inspect the complete recovered project:

```sh
git -C Ilan-Anime-restored switch restored-local-a01870d4b060
```

This backup branch stores the ZIP delivery. The original production commits are
inside the backup; restoring them is separate from publishing them to main.
