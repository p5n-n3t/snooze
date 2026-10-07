# Backend findings re-review

Re-reviewed `p5n-n3t/snooze` at `origin/codex/snooze-command-centre` HEAD `b235f821698eb3be0f5fba81e8a3f8722ca8b191`, against the prior review of `7d675369e8dda7b6f915655e34b4e37731c7b2de`. This was a bounded read-only check of the three original reproductions. I used an archived copy of the reviewed branch, temporary SQLite stores, and fake provider transports/adapters. No provider calls or repository implementation changes were made.

## Results

### 1. Project/account ACL bypass — resolved

**Updated paths:** `snooze/providers.py:22-34,91-95`; `snooze/control.py:43-57,79-80`; `snooze/scheduler.py:129-142`; `snooze/mcp_server.py:19-24`.

Provider accounts now have explicit project authorization rows. Project-scoped listings filter through that relation, account tests and mutations check it, and scheduling considers only accounts authorized for the task's project. The prior reproduction no longer succeeds: with `q-account` authorized only to project `q`, an MCP facade limited to `p` returns no accounts and an `account-config` request against `q-account` is rejected with 403; the account remains enabled. The scheduler's route list is likewise project-filtered.

### 2. Same-revision concurrent task actions — resolved

**Updated paths:** `snooze/control.py:62-83`; `snooze/tasks.py:162-174,198-206`.

Cancellation now rejects an already-pending cancel and updates the attempt only if the task revision still matches, inside the write transaction. Retry passes its expected revision to a transactional transition that also checks for active ownership. The prior concurrent-cancel reproduction now returns one pending response and one 409, calls the adapter once, and increments the task revision once. The same-revision retry reproduction produced one launch and one stale-revision rejection; it did not launch twice.

### 3. Delegated task omitted its approved scope — fixed with an explicit capability limit

**Updated paths:** `snooze/adapters/lightsprint.py:20-32,45-57`; `snooze/policy.py:13-20`; `snooze/queueing.py:12-15`; `snooze/scheduler.py:139-156`.

The adapter now serializes the full approved `TaskSpec` into the remote task description, including its scopes, input reference/hash, and output contract. The old payload reproduction now contains those fields. LightSprint still provides a stack-wide sandbox, so `hard_write_scope` is explicitly unsupported. When a task sets `requirements.hard_write_scope=true`, policy marks that route ineligible; a prompt-scoped task may still route. The adapter requests `autoMerge=false` and instructs the coordinator to review the isolated task-branch diff before applying it.

This closes the original omission and prevents dispatch when a task requires a hard filesystem boundary. It does not create hard per-file isolation for prompt-scoped tasks. Coordinator diff review remains necessary before applying their branch output; Snooze does not automatically merge that output.

## Verification boundary

The three targeted reproductions were rerun against the updated source. No full unit-test suite was run for this bounded re-review. The fake transport confirmed the LightSprint request sets `autoMerge` to `false`; no real provider operation was attempted.
