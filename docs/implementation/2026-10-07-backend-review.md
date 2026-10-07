# Independent backend review

Reviewed `p5n-n3t/snooze` at `codex/snooze-command-centre`, HEAD `7d675369e8dda7b6f915655e34b4e37731c7b2de`, against `717ae2e571a1cd190fee7dbfcb05ecb908cb98a9`. Scope was the backend ownership, scheduling, controls, provider, artifact, notification, MCP and local HTTP paths named in the review brief. No implementation, other repository, provider service, deployment or Neon access was performed.

## Findings

### High — Project-scoped MCP access does not scope provider accounts

**Files:** `snooze/mcp_server.py:17-23,29-36`; `snooze/control.py:52-56`; `snooze/providers.py:22-25,72-74`; `snooze/scheduler.py:127-147`.

The facade checks that a requested project is in its configured allowlist, but `snapshot` returns every provider row through `registry.list_public()`. Provider rows are globally keyed and have no project authorization field. `account-config` then resolves and updates any account ID without checking that the account belongs to the authorized project. The scheduler also considers every provider row for every project. Consequently, a coordinator scoped to one project can read and mutate provider configuration used by another project, and can make an unrelated account eligible for routing.

**Reproduction:** In an isolated SQLite store, register projects `p` and `q`, add a provider account configured with `workspace_id=workspace-q` and `stack_id=stack-q`, and construct `MCPFacade(..., projects=['p'])`. Calling `snapshot` for `p` returns the `q` account. Calling `control` as the `p`-scoped facade with `action='account-config'`, `target_id='q-account'`, and `values={'enabled': False}` returns `confirmed` and disables that account.

**Required repair:** Persist an explicit project-to-account authorization relation. Filter account reads by it, and enforce it in every account control and scheduler route before acting. If accounts are intentionally shared, represent that sharing explicitly and authorize it rather than treating the project allowlist as account isolation.

### High — Delegated execution is broader than the approved task scope

**Files:** `snooze/adapters/lightsprint.py:36-53`; `snooze/scheduler.py:150-155`; `snooze/validation.py:8-24`.

`LightSprintAdapter.launch` creates a remote task with `scope: 'stack'` and sends only the free-form task instructions as its description. It does not serialize the approved task’s `scope_keys`, `input_ref`/`input_hash`, or structured `output_contract`. When an artifact prefix is configured, it appends a generic request to match the “supplied exact output contract,” but that contract is not supplied by this adapter. Local reservation prevents Snooze from assigning overlapping local scopes; it does not constrain what the delegated agent can edit in the remote stack. Artifact validation occurs after execution and cannot undo out-of-scope writes.

**Reproduction:** A fake transport launch with `scope_keys=('path:src/assigned.py',)`, an exact output contract, and instructions `Edit record 17 only.` sends `POST /api/tasks` with `scope='stack'`; the subsequent task description contains no `path:src/assigned.py` or serialized output contract. The agent receives the stack-wide execution context without the local scope fence.

**Required repair:** Carry the approved input, normalized write scope, and exact output contract into the provider request, and enforce a real write boundary in the delegated execution environment. Post-run artifact validation alone is insufficient to protect assigned data.

### Medium — Task revisions do not fence concurrent provider mutations

**Files:** `snooze/control.py:57-80`; `snooze/tasks.py:162-172,196-202`.

`Control.apply` checks `expected_revision` after reading a task, then performs cancellation or retry/resume in separate repository operations. `update_attempt` and `transition` increment the task revision but do not compare it with the revision checked by the caller. Two requests that read the same revision can therefore both mutate the task and issue the provider side effect; the revision is not a compare-and-set fence for these actions.

**Reproduction:** With one active attempt at task revision 2, two concurrent `cancel` calls both use `expected_revision=2`. A barrier after each task read lets both pass the check. Both return `pending`, the adapter receives two `cancel(session)` calls, and the task revision advances to 4. A duplicate provider mutation can also occur for resume/retry if both callers pass their preflight before either changes the row.

**Required repair:** Make the revision comparison and state transition atomic in one transaction, and persist an idempotent action/request identity before making provider calls so a concurrent or retried request cannot repeat the side effect.

## Checks and capability boundary

`python3 -m unittest discover -s tests -q` on the reviewed HEAD: **94 tests passed**. The three reproductions above used an isolated temporary SQLite database and fake transport/adapter; no provider requests were made.

The registered LightSprint adapter reports artifact collection unsupported unless a collector and artifact repository/prefix are configured. Provider reconciliation remains unsupported and requires manual reconciliation; provider idle/failed/completed observations do not establish validated task completion. These are current capability limits, not additional findings.
