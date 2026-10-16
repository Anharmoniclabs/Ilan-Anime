# AnimeStudio workspace

Start the interactive, local scene workspace with:

```bash
python -m studio workspace
```

This opens a native desktop window; it does not start a web server or use a browser. Scene specs, keyframes, and draft renders are read directly from the local Episode 1 workspace. Reference images and scene specs can be opened from the application in the system's default local tools.

The workspace exposes two explicit engine actions: render a single shot as a local draft, or run at most one task from a selected production ledger. Jobs appear in the application and are never retried automatically. Paused runs cannot be resumed from the GUI; resolve blockers and use the CLI's explicit resume process. Paid generation remains governed by `production/policy.json` and each ledger task's budget; the workspace does not modify generation policy or request an external provider directly.

The original read-only production overview remains available with `python production/dashboard.py` on port 8765.

Run its workspace checks with:

```bash
python -m unittest tests.test_workspace -v
```