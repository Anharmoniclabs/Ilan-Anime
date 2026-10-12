# Production dashboard

The local dashboard is a read-only view of the repository's production truth. It summarizes the canonical episode manifest, role registry, persistent run ledgers, asset inventory and optional pipeline plan without modifying any of them.

```bash
python production/dashboard.py
```

Open <http://127.0.0.1:8765>. The server makes no external requests, loads no third-party code, and rejects mutation methods. Use `--port` to choose another local port. `--host` accepts only `localhost` or a loopback IP address; public and LAN bind addresses such as `0.0.0.0` are refused. Requests whose HTTP `Host` header is not `localhost` or a literal loopback address receive `421 Misdirected Request`, preventing a remote DNS name from rebinding the browser to this local service.

For a machine-readable snapshot without starting a server:

```bash
python production/dashboard.py --json
```

The dashboard deliberately distinguishes keyframes, plans, tests, exports, rejected footage, technical review and author creative approval. A keyframe-covered shot is not counted as finished animation. A missing rejection is not treated as approval.

## Data sources

- `production/roles.json`
- `production/runs/*/ledger.json`
- `projects/cemi_episode_01/data/episode.json`
- `production/asset-registry.json`, replayed and hash-chain verified through `AssetRegistry.summary()` and checked against each registered on-disk SHA-256 digest when present
- `projects/cemi_episode_01/data/art_inventory.json`, used only as the legacy fallback when no event registry exists
- `production/pipeline_plan.json` or the episode pipeline plan, when present

The asset view exposes the verified registry state, version, SHA-256 digest and active final-use links. `technical-approved`, `author-approved` and `canonical` remain distinct states. If the canonical registry is malformed, its chain fails, an asset is missing, or an on-disk digest differs, the asset view fails closed with zero registry assets and a visible warning; it does not substitute the legacy inventory. Malformed optional non-canonical records appear as warnings instead of crashing the whole dashboard. Only normalized summaries and repository-relative source paths are exposed by `/api/studio`; arbitrary repository files and host agent IDs are not served.

## Verification

```bash
python -m unittest tests.test_dashboard -v
```

The tests cover canonical counts, paused runs, default event-registry replay, on-disk tamper detection, version/hash/final-use visibility, role and asset visibility, safe JSON output without host agent IDs, loopback-only binding and Host-header enforcement, security headers, traversal resistance and refusal of write methods.
