# Real host-agent handoff

`production/runtime.py` is a ledger, not an agent host. Tasks that must prove a
real delegated creator and reviewer set `require_host_bindings: true`. Tasks
without that field keep the lightweight local-fixture behavior.

The coordinator uses this order:

1. Add and dispatch the task with a ledger alias.
2. Spawn the creator through the actual host.
3. Record the returned host identity with `host_handoff.py bind-creator`.
4. Require that exact host identity in the creator result as `host_agent_id`.
5. Submit the result through `runtime.py`; this advances the creator binding.
6. Spawn a worker for the designated reviewer role and record it with
   `bind-reviewer`.
7. Review using that exact reviewer role and host identity.

The creator and reviewer host identities must be distinct. A ledger alias is
not accepted as proof of a host agent, and an arbitrary reviewer name cannot
approve an opted-in task. The designated reviewer still comes from
`production/roles.json`.

The ledger transition owns `submitted` and `completed` binding states. A host
interruption changes the active creator or reviewer binding to `interrupted`,
pauses the ledger, and never retries or reassigns it automatically. Resuming a
run does not revive an interrupted binding or permit it to submit/review; it
only permits the coordinator to create a separately identified revision task
after the user explicitly approves the next action.

Ledger and registry files are each written with atomic replacement under a
single-coordinator rule. The registry is saved immediately before the matching
ledger transition. A process failure between those writes produces a
fail-closed state mismatch that validation reports for manual reconciliation;
it never authorizes work or approval.

These records are orchestration evidence only. They do not authenticate a host,
enforce filesystem/tool restrictions, meter budgets, or provide an OS sandbox.
