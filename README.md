# Heralds of the Cemí — Episode 1

Start with [START_HERE.md](START_HERE.md) for daily commands, folder ownership and completion steps, or open the [searchable shot navigator](production/navigation/index.html). Refresh its file checks with `.venv/bin/python -m studio navigate --probe`.

A 128-shot, 18:50 (27,120 frames, 24 fps, 16:9) animated episode, produced with a ledger-driven studio engine, the Craft apps and department agent skills.

Approved style and motion reference: the [35-second opening](episode-01/build/take-02/opening-assembly.mp4) and its [workflow](episode-01/WORKFLOW.md). Current honest status: [docs/STATUS.md](docs/STATUS.md). Where everything lives: [docs/REPOSITORY_MAP.md](docs/REPOSITORY_MAP.md).

## Where things are

| Path | What it is |
|---|---|
| `studio/` | The engine and CLI (`python -m studio`) |
| `production/` | Runs, task evidence, asset registry, policy, dashboard, desktop workspace |
| `projects/cemi_episode_01/` | Script, shot timing, original art |
| `episode-01/` | The approved 1990s cel workflow and its takes |
| `tests/` | Regression tests |
| `.agents/skills/` | Department agent skills |
| `archive/` | Older prototypes, preserved (including the old Fal "Anime Motion" tool) |

## Setup

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # numpy, Pillow; FFmpeg required
```

## Common commands

```bash
.venv/bin/python -m studio status              # episode, runs, spend
.venv/bin/python -m studio workspace           # native desktop scene workspace
.venv/bin/python -m studio picture status      # per-shot picture-draft runs
.venv/bin/python -m studio animatic --out DIR  # full-length timing animatic (not animation)
.venv/bin/python -m studio craft doctor --out DIR
python production/dashboard.py                 # read-only production dashboard
```

Tests (name modules explicitly; `tests/` is a package):

```bash
.venv/bin/python -m unittest tests.test_studio tests.test_workspace
```

## Rules that matter

- Generation is off with a $0 cap in `production/policy.json`; only the owner changes it.
- Technical review is not author approval. Only Luis approves creative work.
- Keep approved references and earlier takes; new takes get new directories.
- Videos are not in Git LFS. `production/lost-lfs-files-20261015.json` lists 144 earlier files whose bytes were never uploaded and cannot be recovered.
