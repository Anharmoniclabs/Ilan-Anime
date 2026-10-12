---
name: anime-studio
description: Coordinate individually spawned animation-production agents with shot-scoped tasks, role skills, evidence review, and user-controlled recovery. Use for multi-agent anime preproduction, animation, and postproduction in AnimeStudio.
---

# Coordinate the studio

Locate the AnimeStudio checkout; read its `AGENTS.md`, `docs/STATUS.md`, `docs/STUDIO_STANDARD.md`, `production/README.md`, `production/roles.json`, and `production/art_direction.json`. Resolve relative paths against that checkout. Ask for the checkout if absent. Do not invent missing assets or approvals.

1. Build or validate the shot DAG with `production/pipeline.py`, then translate ready stages into ledger tasks with exact shot IDs, objective, existing approved inputs, dependencies, output directory, acceptance criteria and zero-dollar budget. Inspect both CLIs first. Never bypass unresolved gates.
2. Discover the host's actual delegation capability. When `collaboration.spawn_agent` is available, dispatch one ready ledger task and pass its generated prompt to one new agent. Else use only a documented equivalent. If delegation is unavailable, stop and explain; never impersonate multiple agents in one response.
3. Read the selected role's complete `SKILL.md` and require the worker to read it too. Include the task envelope and explicit input paths. Each worker owns only its task output directory, cannot delegate further, and returns the specified result object.
4. Spawn only independent ready tasks within the host's free slots and ledger limit. Bind returned host agent IDs with `production/host_handoff.py`. Do not launch every role merely to fill a roster. A voice agent without approved voice tools reports blocked, not recorded audio.
5. Inspect artifacts and evidence before submission. Assign a separate review task to the reviewer in `roles.json`. Record actual reviewer identity and findings; a creator cannot approve their work. For visual assets, validate the mode-specific art report and register the exact file/version/hash. Technical approval never implies Luis's author approval.
6. On interruption, missing permission/input, budget exhaustion, or ambiguous external results, pause dispatch and checkpoint. Ask before resuming or repeating external actions. Never auto-reconnect, schedule retries, switch providers, or incur costs. After approval inspect the original action's state to prevent duplicates.
7. Report completed, rejected and blocked work separately. Require actual motion review with timecodes before claiming an approved animated shot. Tests, atlases, contact sheets and successful exports alone cannot establish animation quality. Run `production/studio_validate.py` and report architecture readiness separately from episode readiness.

Use supplied still artwork for purposeful replacement drawings, acting, contact, secondary action, water/FX and compositing. Preserve stable anatomy and rigid props. Do not use Higgsfield, whole-painting deformation or camera moves as substitutes for character action.

Treat write scopes/tool budgets as instructions in native shared-workspace agents, not a security sandbox. The ledger validates transitions and submitted paths, not arbitrary shell/tool calls. Hard boundaries require isolated workspaces and host-enforced permissions.

Keep these skills in the user-requested Git repository. Do not claim global installation or native-tool registration from a repository commit alone.
