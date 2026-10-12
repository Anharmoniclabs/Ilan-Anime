# Complete-shot production pipeline

`production/pipeline.py` converts a shot specification into a deterministic stage DAG and task envelopes compatible with `production/runtime.py`. It is a production contract, not an image generator, agent spawner or approval shortcut.

## Production path

The complete path is:

1. script supervision and author-approved timing resolution;
2. pipeline build contract and asset intake register;
3. timed boards and specialist layout;
4. character, prop, art and color design;
5. registered background painting and clean plates;
6. a bounded rig/no-rig decision with replacement-drawing limits;
7. registered key drawings and the animation-supervisor gate;
8. breakdowns, in-betweens and specialist cleanup;
9. specialist ink and paint plus drawn effects;
10. compositing;
11. sound plan, authorized voice/no-dialogue determination, dialogue edit, SFX and music;
12. final mix and picture edit;
13. delivery asset manifest;
14. independent QA and final author approval.

The template contains 27 bounded tasks. Every task names exact shots, one specialist role, an independent designated reviewer, dependencies, repository inputs, an exact output directory, artifact/evidence contracts, acceptance criteria and a zero-dollar tool budget. The existing ledger remains the state authority. `pipeline.py` does not weaken its pause, review or path checks.

Tasks that create or judge visual material carry an explicit `art_direction_mode`, causing workers to read `production/art_direction.json` and its canonical document. `script-timing` and final `qa` preserve `requires_author_approval` when emitted through `ledger_task()`. Consequently, the existing ledger will not release their dependents on technical approval alone: it requires Luis's separately recorded author decision.

## Gates are deliberately different

A **technical gate** is an independent agent review. The creator and reviewer must have different roles and agent identities. Review requires real files, the required artifact kinds, specific evidence for every evidence category, and an approval decision. Specialist reviewer pairings come directly from `production/roles.json`; for example cleanup and effects report to the animation supervisor, ink/paint reports to the color designer, rig decisions report to the CG director, and sound crafts report to the sound director.

An **author gate** records Luis's creative decision after he has been shown the relevant material. A technical pass cannot fabricate or imply author approval. The pipeline has two author gates:

- `timing-author-approval`, before boards and production drawings;
- `final-author-approval`, after QA and before a render is called canonical.

The author gate records evidence such as the selected option, what was viewed and the approval reference. It is not an agent role and is not self-approved by the coordinator.

The timing gate cannot be approved while `timing.status` is `unresolved`. Approval is restricted to `luis-m-minier` and is bound to the exact script-timing task, a repository JSON decision record, that record's SHA-256, the exact record Luis viewed, a durable approval reference, and one declared choice for every recorded timing conflict. The record content must exactly match the pipeline, shots and selections. Arbitrary evidence strings cannot release boards or production.

The final gate is stricter than a list of approval strings. It is bound to `luis-m-minier`, the exact QA task, the exact artifact path and SHA-256, the artifact Luis viewed, and a durable approval reference. The same path and digest must resolve to a canonical production asset with an active final-use link and a matching Luis author-approval record in the tamper-checked registry. Placeholder evidence such as `x/y/z` cannot unlock delivery.

Episode release accounting also requires the real `quality-review` task emitted by this pipeline, not an arbitrary task whose name ends in `-qa`. Its submitted result records `pipeline_id`, `qa_report: {path, sha256}`, and `release_asset_sha256s`; those digests must exactly equal the canonical final picture/audio assets for the task's shots. The task must retain its edit, final-manifest and pipeline-contract dependencies, completed creator/reviewer host bindings, and Luis's separate author approval.

## Full-scene action, not a moving still

Each specification must independently describe character, prop, environment, effects and camera action. Character and environmental action are mandatory. Camera action may be empty, but it can never be the only movement. The keys, effects, composite, edit and QA contracts explicitly reject whole-painting deformation, optical-flow performance, sliding cutouts, unexplained holds and camera-only substitutes.

`source_inputs` are restricted to repository text/data (`.md`, `.json`, `.csv`, `.txt`, `.fountain`). Media, binaries, and anything under `rejected/`, `renders/`, or `replacement_cels/`—or named `unapproved`—are refused. A caller cannot relabel a file by writing `"status": "approved"`; the legacy `assets` field is rejected outright.

Production media uses `production_assets`. Every entry supplies an exact asset ID, version, SHA-256 and active final-use ID. The builder verifies the hash chain in `production/asset-registry.json`, checks registered files on disk, requires canonical state and production mode, checks the exact final-use link, and independently hashes the requested file. Existing rejected videos and replacement atlases may remain as audit evidence, but they are not production inputs. Asset-manager stages verify initial provenance and final source-to-delivery hashes; neither may creatively approve art.

An unregistered image may appear only in `comparison_references` with purpose `visual-style-comparison-only` and `production_input: false`. It is reported for comparison but never added to a worker's production inputs. The supplied style overview uses this narrow path.

The character-rigger stage may approve a narrowly bounded rig, but it may also—and for substantial shot-specific acting often should—deliver an explicit **no-rig recommendation**. That decision sends view changes, pressure, balance and complex contacts to registered replacement drawings. It cannot use rubber-sheet deformation to make a flattened image perform.

The audio branch is similarly explicit. It separates direction, authorized voice performance (or a documented no-dialogue result), dialogue editing, SFX/ambience, original music or intentional silence, and final mixing. Missing permissions, recordings and rights remain blockers; no specialist may invent dialogue, clone a voice or disguise temporary sources.

## S01-11 / S01-12 gate

The example at `production/examples/s01_11_12_pipeline.json` captures the actual full-scene action but intentionally leaves production blocked on three contradictions:

- the shot rows total 24 seconds, while the showcase heading says 22 seconds;
- the shot rows specify drawings on 2s, while the showcase note says characters on 3s and FX on 2s;
- the showcase events cover relative frames 0–168, while the two shots contain 576 frames.

The software does not guess. Only the initial script/timing task is ready. Downstream production remains blocked until the timing options are presented to Luis and the selected duration, exposure policy and mapping are recorded.

## Build and inspect

From the repository root:

```bash
python production/pipeline.py production/examples/s01_11_12_pipeline.json \
  --ledger-tasks-dir production/generated/s01_11_12
```

The command prints the complete plan and optionally writes one `Ledger.add` JSON object per task. Generated task inputs include approved source material and upstream task directories. `Ledger.dispatch` will therefore refuse a downstream task until its dependencies have been completed and their directories exist.

Run verification with:

```bash
python -m unittest tests.test_pipeline -v
python -m unittest discover -s tests -v
```

Passing tests proves the runtime validators, dependency, boundary and gate behavior exercised by those tests. Checked-in JSON Schema files are parsed for publication, while the Python runtime validators remain authoritative. None of this proves visual quality. Final animation must still be viewed in real-time and frame-stepped at contacts, occlusions and cuts.
