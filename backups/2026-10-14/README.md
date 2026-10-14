# Ilan-Anime local production backup — 2026-10-14

[Repository map](../../docs/REPOSITORY_MAP.md) · [Current status](../../docs/STATUS.md)

**Incomplete — checked 14 October 2026.** [manifest.json](manifest.json) records `complete: false`, five saved ZIP volumes and `expected_volumes: 299`. The five listed ZIPs are present in this checkout. This set cannot currently restore the complete saved project. The restore instructions below apply only after the full set is available and the manifest records completion.

The planned complete volume set preserves four historical local commits, ending at
`a01870d4b0609adb9236d2e9262eac3b23b720dd`. Together with the base Git
history through `e10efd46ea5162d2f3396322b1cd74a1b3b6bc80`, the complete set is intended to restore the
saved project: 39,567 tracked files and symlinks.

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

These files came from the backup delivery branch. The partial volume set is now
present in this checkout; neither local presence nor this README verifies remote
completeness. Restoring historical commits is separate from publishing them to main.
