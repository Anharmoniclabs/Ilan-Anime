# Art asset registry and approval pipeline

`production/asset_registry.py` is the source-of-truth gate between generated or
drawn files and the final edit. It does not decide whether art is good. It records
the file that was reviewed, the evidence supplied by technical and author review,
and whether that exact file version may be linked into final use.

The registry is intentionally separate from the production task ledger. A task
being approved means its bounded assignment passed its designated production
review. It does **not** make every artifact canonical. Each artwork, sound file,
layout, exposure sheet, or render must pass the asset states below.

## State model

| State | Meaning | May enter final edit? |
|---|---|---:|
| `exploratory` | A study, generated candidate, test, or unfinished drawing | No |
| `submitted` | Creator believes the version is ready for technical review | No |
| `technical-approved` | Registration, matte, geometry, continuity, file integrity, or playback checks passed | No |
| `author-approved` | Luis approved the creative result and Cemí art direction | No; canonicalization is still explicit |
| `canonical` | The approved version is the production source of truth | Yes |
| `rejected` | The exact version must not be used | No |

The enforced happy path is:

`exploratory → submitted → technical-approved → author-approved → canonical`

Technical approval requires a `technical` approval record from an approver whose
stable ID differs from the asset provenance `creator`. Author approval requires a
separate `author` record issued by `luis-m-minier` in the `author` role. Neither
implies the other. Every approval binds to the registered asset SHA-256, so a
review for one file cannot approve a changed file or another version. Rejection is a
terminal state for that version; create a new version for a correction. A linked
canonical version must be explicitly unlinked before it can be rejected, so the
final edit cannot silently point at rejected work.

## Stable identity and immutable versions

An `asset_id` names the continuing production concept, such as
`s01-11.beheto-drum-contact`. Its integer version identifies one exact file.
Registering another file under the same ID appends the next version; it never
replaces version 1. Use `supersedes` to identify the earlier version a redraw is
intended to replace.

Each registered version includes:

- repository-relative file path and SHA-256 content hash;
- kind and production mode (`source`, `reference`, `work-in-progress`, or
  `production`);
- declared shot use;
- source provenance, creator, license, and upstream asset versions;
- character, costume, prop, time, and location continuity fields;
- initial state and optional superseded version.

Absolute paths, hidden/private local paths, traversal, signed/query URLs, URL
credentials, and local network URLs are rejected. Registry paths stay portable
and never expose a workstation or temporary upload location.

The registry rereads the on-disk file and compares it with the registered digest
before technical approval, author approval, canonicalization, and every final-use
link. Missing, symlinked, or modified files fail closed at each gate.

Final-use authorization is shot-scoped. `verify()` exposes each active use as
`{asset_id, version, shots}`, and `summary()` preserves the same `shots` list.
Pipeline shots must be a subset of both the registered asset shots and the active
final-use link shots. A canonical asset cleared for `S01-11` cannot be reused in
`S01-12` merely by referencing the same asset ID or digest.

## Tamper evidence and write behavior

The JSON file is an append-only, SHA-256 hash-chained event log. Registration,
state transitions, final-use links, and unlinks append events. Existing events are
never edited by the API. Writes use a flushed temporary file plus `os.replace`, so
a partially written registry does not replace the prior valid file.

This provides tamper evidence, not cryptographic identity or a multi-writer
database. Keep one coordinator as the registry writer. Git review/signing and
normal repository permissions remain the outer control boundary.

## Commands

From the repository root:

```bash
python production/asset_registry.py --help
python production/asset_registry.py init
python production/asset_registry.py register production/new-asset.json
python production/asset_registry.py transition s01-11.beheto-drum-contact 1 submitted
python production/asset_registry.py transition s01-11.beheto-drum-contact 1 technical-approved \
  --approval production/technical-approval.json
python production/asset_registry.py transition s01-11.beheto-drum-contact 1 author-approved \
  --approval production/examples/approval_record.json
python production/asset_registry.py transition s01-11.beheto-drum-contact 1 canonical
python production/asset_registry.py link-final picture-lock.s01-11 \
  s01-11.beheto-drum-contact 1 S01-11
python production/asset_registry.py verify --check-files
python production/asset_registry.py show
```

The registration JSON supplies the keyword fields accepted by `register`, except
`version` and `sha256`; those are assigned from registry history and the actual
file. A registration document looks like this:

```json
{
  "asset_id": "s01-11.beheto-drum-contact",
  "path": "projects/cemi_episode_01/assets/replacement_cels/beheto_eight_poses.png",
  "kind": "replacement-cel-sheet",
  "mode": "work-in-progress",
  "shots": ["S01-11"],
  "provenance": {
    "origin": "replacement-cel pass",
    "creator": "cemi-production-team",
    "license": "project-owned",
    "source_assets": [],
    "notes": "Pending registration and matte review."
  },
  "continuity": {
    "character_ids": ["beheto"],
    "costume_ids": ["beheto-river-v1"],
    "prop_ids": ["drum-v1", "canoe-lead-v1"],
    "time": "moonless night before first bell",
    "location": "river lead canoe"
  },
  "initial_state": "exploratory",
  "supersedes": null
}
```

`production/examples/asset_registry.json` records the current Beheto pose sheet
as exploratory. Its real file hash is recorded, but that registration is not an
approval and creates no final-use link. `production/examples/approval_record.json`
shows the author-approval shape; examples do not grant approval to the artwork.

JSON Schemas live in `production/schemas/`. Runtime validation remains
authoritative because it additionally checks transition ordering, the event hash
chain, existing source versions, on-disk hashes, and final-use eligibility.

## Review evidence for Cemí

Technical evidence should name the checks actually performed: registration
landmarks, model identity, rigid canoe/drum/paddle geometry, hand contact, matte
edges, alpha/color mode, exposure timing, frame-step behavior, continuity, and
file/hash verification. Successful export alone is insufficient.

Author evidence should identify the reviewed version and exact SHA-256 plus the creative decision:
likeness, acting, hand-drawn-derived line quality, dark navy/steel and charcoal
shadows, amber rim light, restrained anime treatment, cultural detail, staging,
and whether the motion feels alive without warping. The author approval record is
never fabricated from technical checks or inferred from silence.
