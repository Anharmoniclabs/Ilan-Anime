# Bounded animation team

Start with `skills/anime-studio/SKILL.md`. Each department has an independent skill listed in `roles.json`; the coordinator spawns one real worker per ready task. Skills supply duties and review contracts. The host supplies spawning and tools. These additions do not automatically register a ChatGPT plugin or install skills in every host.

| Stage | Roles | Handoff |
|---|---|---|
| Preproduction | Director, producer, episode director, storyboard | Script locks, shot objectives, dependency schedule, timed boards |
| Visual development | Character designer, art director, color designer | Model/prop sheets, layouts, palette and lighting continuity |
| Animation | Animation supervisor, key animator, inbetweener, CG director | Keys, breakdowns, registered exposures, rigid-prop/contact checks |
| Sound | Sound director, voice performer, SFX artist | Exact dialogue takes, cue sheets, original/licensed stems and sync evidence |
| Postproduction | Compositor, editor, quality reviewer | Layered renders, continuity edit, timestamped defects |

The director/producer/episode-director meeting is a coordination checkpoint, not permission to edit the same script simultaneously. Workers propose changes in their own directories; the coordinator integrates reviewed outputs.

## Task boundaries

Assign exact shot IDs, existing input paths, one objective and one output directory. No worker may overwrite source art, delegate, publish, change providers or spend money. Read-only inspection and local verification are the default budget. Generation, voice synthesis and external rendering require separately authorized available capabilities and relevant skills.

The persistent ledger in `runtime.py` validates dependencies, transitions, concurrency and submitted paths. It does **not** execute a model, enforce an OS sandbox or intercept tools. One coordinator owns the ledger. Hard isolation requires separate workspaces and host-level permissions.

```bash
python production/runtime.py --help
python -m unittest discover -s tests -p 'test_production_runtime.py' -v
```

For a new local run (from repository root):

```bash
python production/runtime.py --run example init
python production/runtime.py --run example add production/example-task.json
python production/runtime.py --run example ready
python production/runtime.py --run example dispatch motion-plan --agent-id motion-worker
```

The final command reserves a task and prints its worker prompt; pass that prompt to the host's real spawn tool. `motion-worker` is a ledger alias, not a generated host ID. Record the alias-to-host-ID mapping. Add dependent tasks in dependency order. Submit the worker's result JSON with `submit PATH`; review with `review TASK --reviewer-role ROLE --reviewer-agent-id ALIAS --decision approve|reject --evidence TEXT`. Only an actual separate reviewer can supply that evidence.

Use `pause REASON` when interrupted. After receiving real user permission, record it with `resume --approval 'APPROVE RESUME example'`; the string is a coordinator record, not authentication or permission by itself. Resume never resets blocked/rejected tasks. Create a new revision task when a correction is authorized.

## Host connection and recovery

In a session exposing `collaboration.spawn_agent`, pass the dispatched prompt to that real tool, then message/wait using its returned ID. The CLI does not fake these calls. Map the same envelope/results to another host's documented delegation tool. If none exists, report the missing capability; sequential role-play is not spawned agents.

Keep a handoff record with ledger path, task ID, host agent ID, input versions, output locations and last confirmed state. Never silently rerun a running task after disconnect. Pause, ask the user, inspect existing outputs/jobs, then resume only with approval. No scheduled automation or automatic reconnection is included.

Make this repository's `skills/` available through the target host's supported skill-discovery mechanism, or explicitly ask its agent to read `skills/anime-studio/SKILL.md`. Portability of the files does not guarantee every host supports multi-agent execution.

Official references checked 2026-10-12:

- [OpenAI multi-agent delegation](https://developers.openai.com/api/docs/guides/agents-api/multi-agent): the harness supplies delegation tools when enabled.
- [OpenAI skills](https://developers.openai.com/api/docs/guides/tools-skills): skills provide reusable instructions and files; discovery depends on the runtime.

## Animation acceptance

Planning is not animation. Review rendered sequences at speed and frame-step contact/occlusion transitions. Record timecodes for model drift, warping, hand/paddle contact, hull rigidity, wake movement, matte seams and unintended holds. Existing rejected footage stays rejected until a new reviewed render exists.
