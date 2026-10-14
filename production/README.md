# Production workspace

[Home](../README.md) · [Repository map](../docs/REPOSITORY_MAP.md) · [Current status](../docs/STATUS.md)

This directory contains both production-control code and saved creative work. Use these entry points before browsing individual task folders:

| Need | Location |
|---|---|
| Every run, package and control module explained | [Production map](../docs/REPOSITORY_MAP.md#production-shelves-and-packages) |
| Current episode inspection and editable timeline | [Episode wiring](runs/episode1-full-picture/tasks/episode-wiring/README.md) |
| Selected 128-shot still pass | [Shot index](runs/episode1-anime90s-scenes/shot-index.json) |
| New cast artwork and review books | [Cast run](runs/episode1-anime90s-cast/) |
| Amaia library, puppet and opening source shortcuts | [Current shelf](current/README.md) |
| Latest action-drawing blockers | [Action checkpoint](runs/episode1-action-completion-20261014/checkpoints/progress.json) |
| Browse earlier videos | [Video library](video-library/index.html) |

`runs/<run>/tasks/<task>/` holds editable sources and results; `reviews/` holds independent decisions; `ledger.json` records state and dependencies. Preserve earlier versions and read exact review records before reuse. A run's name or a technically approved draft does not imply final author approval.

## Bounded animation team

Start with `.agents/skills/anime-studio/SKILL.md` (Codex discovers skills in `.agents/skills`). Each department's skill is **generated** from `roles.json` by `python production/build_skills.py`; shared rules live once in `WORKER_CONTRACT.md`. The Codex runner (`python -m studio run`, see `docs/STUDIO_RUNTIME.md`) starts one real `codex exec` worker per ready task and a separate reviewer session per submission.

| Stage | Roles | Handoff |
|---|---|---|
| Direction and continuity | Director, producer, episode director, script supervisor, storyboard | Canon/timing decisions, shot objectives, dependency schedule, timed boards |
| Visual development | Layout artist, character/prop designers, art director, background painter, color designer | Registered layouts/model sheets, final plates, palettes and lighting continuity |
| Animation | Animation supervisor, key animator, inbetweener, cleanup artist, ink/paint artist, effects animator, character rigger, CG director | Stable keys, breakdowns, cleanup, painted cels, bounded rigs/FX and registered exposures |
| Sound | Sound director, voice performer, dialogue editor, SFX artist, composer, mix engineer | Authorized takes, edited dialogue, cue sheets, original/licensed stems and final sync mix |
| Post and operations | Compositor, editor, pipeline TD, asset manager, quality reviewer | Layered renders, manifests/hashes, continuity edit and timestamped QA |

The director/producer/episode-director meeting is a coordination checkpoint, not permission to edit the same script simultaneously. Workers propose changes in their own directories; the coordinator integrates reviewed outputs.

## Task boundaries

Assign exact shot IDs, existing input paths, one objective and one output directory. No worker may overwrite source art, delegate, publish or change providers. Spending happens only through `python -m studio generate`, within `policy.json` (off by default) and the task's `max_cost_usd`.

The persistent ledger validates dependencies, transitions, author gates, concurrency and submitted paths. The host-handoff registry binds ledger aliases to actual spawned agents. Neither executes a model, enforces an OS sandbox or intercepts tools. One coordinator owns each run. Hard isolation requires separate workspaces and host-level permissions.

```bash
python production/runtime.py --help
python production/studio_validate.py
python production/dashboard.py
python -m unittest discover -s tests -v
```

For a new local run (from repository root):

```bash
python production/runtime.py --run example init
python production/runtime.py --run example add production/example-task.json
python production/runtime.py --run example ready
python production/runtime.py --run example dispatch motion-plan --agent-id motion-worker
```

The final command reserves a task and prints its worker prompt; pass that prompt to the host's real spawn tool. `motion-worker` is a ledger alias, not a generated host ID. For host-bound tasks, bind the returned creator ID with `host_handoff.py bind-creator`; after submission, spawn and bind the separate designated reviewer with `bind-reviewer`. The submitted result must include the real creator `host_agent_id`, and `review --reviewer-agent-id` must receive the bound reviewer's real host ID. See `docs/HOST_HANDOFF.md` for the exact sequence.

For a task marked `requires_author_approval`, technical approval does not unlock dependents. After Luis reviews that exact deliverable, record the real decision with `author-review`; a rejection stays blocked and a revision gets a new task and asset version.

Use `pause REASON` when interrupted. After receiving real user permission, record it with `resume --approval 'APPROVE RESUME example'`; the string is a coordinator record, not authentication or permission by itself. Resume never resets blocked/rejected tasks. Create a new revision task when a correction is authorized.

## Host connection and recovery

In a session exposing `collaboration.spawn_agent`, pass the dispatched prompt to that real tool, then message/wait using its returned ID. The CLI does not fake these calls. Map the same envelope/results to another host's documented delegation tool. If none exists, report the missing capability; sequential role-play is not spawned agents.

Use `host_handoff.py` for ledger alias, host and actual agent identity. Never silently rerun a running task after disconnect. Mark the binding interrupted, pause, ask the user, inspect existing outputs/jobs, then resume only with approval. No scheduled automation or automatic reconnection is included.

Codex reads this repository's `.agents/skills/` automatically; for other hosts, make it available through the target host's supported skill-discovery mechanism, or explicitly ask its agent to read `.agents/skills/anime-studio/SKILL.md`. Portability of the files does not guarantee every host supports multi-agent execution.

Official references checked 2026-10-12:

- [OpenAI multi-agent delegation](https://developers.openai.com/api/docs/guides/agents-api/multi-agent): the harness supplies delegation tools when enabled.
- [OpenAI skills](https://developers.openai.com/api/docs/guides/tools-skills): skills provide reusable instructions and files; discovery depends on the runtime.

## Animation acceptance

Planning is not animation. Review rendered sequences at speed and frame-step contact/occlusion transitions. Record timecodes for model drift, warping, hand/paddle contact, hull rigidity, wake movement, matte seams and unintended holds. Existing rejected footage stays rejected until a new reviewed render exists.

The full release standard is `docs/STUDIO_STANDARD.md`. Art reports use `production/art_direction.json`; file promotion uses `asset_registry.py`; complete shot work uses `pipeline.py`. The local dashboard is informational and read-only. None of these tools may infer beauty or author approval from tests.

## Local drawing backend

The coordinator can use `python -m production.comfy.local` to submit approved-reference image jobs to self-hosted ComfyUI, collect exploratory assets into the shared registry and retain manual recovery after interruptions. See [setup, commands and limits](../docs/COMFY_LOCAL.md). This does not auto-spawn workers, approve drawings or complete animation tasks.
