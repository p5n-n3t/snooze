# Snooze backend release safety review

**Reviewed:** `p5n-n3t/snooze` commit `eaf4db93fe186bdc4d80151d9ac9bf5d983ff555`, compared with `717ae2e`.

**Scope:** Backend implementation only. I used the approved Command Centre architecture note and the Global Constraints and acceptance cases in the Command Centre, control-plane, and analytics plans. Pending UI, assets, and operator-doc changes were not graded as implemented.

**Method:** Static review plus `python3 -m unittest discover -s tests -q` against an archive of the exact reviewed commit in `/tmp` (159 tests passed). I also ran isolated fake-adapter checks and a loopback-only redirect check with a dummy credential; no live provider or external-account calls were made.

## Findings

### Important — Emergency stop can race past a reserved launch

**Location:** `snooze/scheduler.py:158-170`; `snooze/tasks.py:139-143`.

`Scheduler.tick` reads settings once, checks pause/stop at line 158, then reserves the task and calls `adapter.launch` without checking whether the policy revision changed after reservation. `TaskRepository.reserve` fences the policy revision only at reservation time. A stop acknowledged in the gap can therefore be followed by a provider launch using the stale settings snapshot. A fake-adapter reproduction toggled `emergency_stop` immediately after the `starting` transition and observed one launch.

**Effect:** The “persist immediately” emergency stop and pause semantics do not hold across the reservation-to-network boundary. The same stale-settings window exists between `_recover`'s pause check and `adapter.resume`.

**Fix:** Revalidate the policy revision and dispatch gate at the last safe point before every launch/resume, using a durable dispatch generation or equivalent gate that a stop invalidates. Add deterministic race tests for stop/pause after reservation and before provider I/O.

### Important — Recovery resumes a disabled account

**Location:** `snooze/scheduler.py:76-95`.

`_recover` checks project authorization, pause/stop, backoff, retry count, and resume capability, but never checks the account’s current `enabled`, health, quota, or cooldown state before calling `adapter.resume`. In an isolated reproduction, disabling the account after launch and then returning provider status `failed` still sent one resume request.

**Effect:** Disabling an account does not stop automatic recovery from issuing new provider mutations against it, and recovery can ignore quota or cooldown changes that would exclude a new route.

**Fix:** Apply a current account eligibility/budget check to resume operations as well as fresh reservations. Persist a blocked reason when the account is disabled, unhealthy, outside scope, cooling down, or below reserve.

### Important — Failed and ambiguous attempts have no supported ownership-resolution path

**Location:** `snooze/scheduler.py:73-74, 82-83, 108-114`; `snooze/tasks.py:187-194`; `snooze/control.py:65-72`.

Invalid output and exhausted recoveries move an attempt to `blocked` without releasing its scope. Ambiguous launches remain active when reconciliation is unsupported. `TaskRepository.release` accepts manual ownership-resolution evidence, but no HTTP/MCP control action exposes that operation; retry rejects any active attempt, and reassign is explicitly unsupported. An isolated invalid-artifact reproduction left the attempt active and returned HTTP-style status 409 on retry.

**Effect:** One validation failure, exhausted retry budget, or ambiguous launch can permanently occupy the task’s scope and account/project capacity. A partially created provider task can also become unresolvable because its provider task ID is not retained until `launch` returns.

**Fix:** Add an audited operator reconciliation action that records evidence and explicitly confirms provider inactivity/cancellation or manual ownership resolution before releasing the lease. Preserve remote task identifiers as soon as they are created; never make lease expiry alone sufficient to release ownership.

### Important — Authenticated LightSprint requests forward credentials across redirects

**Location:** `snooze/transport.py:35-46`.

The transport adds the configured `Authorization` header and calls the default `urllib.request.urlopen`, which follows redirects. A local two-server reproduction returned a redirect to a second origin and observed the dummy `Authorization: Bearer ...` header at the redirect target.

**Effect:** A redirect response from the configured LightSprint endpoint can disclose the workspace credential to a different host. The analytics and notification transports explicitly block redirects; this transport does not.

**Fix:** Use a no-redirect opener for authenticated provider calls and fail closed on every redirect. If redirects are ever required, validate the final scheme, hostname, and port before forwarding credentials.

### Important — Quota values are checked but never reserved against concurrent work

**Location:** `snooze/providers.py:97-103`; `snooze/policy.py:39-46`; `snooze/tasks.py:134-153`.

The account snapshot returns the same configured quota override on every scheduling pass. Policy rejects only when that value is at or below the reserve; transactional reservation enforces task/account/model concurrency but does not reserve or decrement quota. A fake-adapter reproduction with a one-credit override, zero reserve, and two approved tasks launched both tasks concurrently against that same single-credit snapshot.

**Effect:** The configured reserve is a threshold, not a maintained budget. Several tasks can be dispatched based on one unchanged balance, so Snooze cannot claim to keep usage within the configured quota/reserve.

**Fix:** Track a durable per-account/model budget reservation alongside task claims and reconcile it from measured cost or a fresh quota observation. When task cost cannot be bounded, make that limitation explicit and require an operator policy that cannot be mistaken for enforced remaining budget.

### Minor — Session-child analytics reports are unavailable and not exposed by HTTP

**Location:** `snooze/analytics_engine.py:271-279, 332-340`; `snooze/history_api.py:10-12, 70-84`.

The engine contract accepts `session_children` as a list, but `_normalize` only wraps `usage_top_sessions`; it then rejects every non-dict normalized result. A fake valid list response returned `unavailable/contract_mismatch`. Separately, the history HTTP allowlist omits all `session_*` kinds, and its filter parser has no `session_id` field, so the planned session drill-downs cannot be requested through that API.

**Effect:** Session child relationships cannot be consumed through the implemented engine/history surface even when the source returns valid data.

**Fix:** Normalize list responses into a documented safe DTO and add a project-scoped session identifier to the HTTP/MCP contract with matching authorization and tests, or keep these reports explicitly unsupported.

### Minor — Custom service ports are not persisted for `snooze open`

**Location:** `snooze/service.py:22-33`; `snooze/launch.py:37-45, 52-67`.

`install_service` writes the selected port into the systemd unit but stores only the service name in `project.json`. Later, `open_dashboard` probes its CLI port (default 8765); `start_daemon` starts the registered unit and ignores that port. Installing the service on 9000 and then running the default `snooze open` starts the service on 9000 but waits for 8765 until readiness times out.

**Effect:** The documented one-command open flow fails for a valid non-default service port unless the operator remembers to pass the same port each time.

**Fix:** Persist the registered service port with the service name and use it as the default for `open`, or inspect the registered unit’s configured port before probing.

## Review outcome

The fake/unit suite is green, but the race, recovery, ownership, credential-redirect, and budget findings affect release safety and should be addressed before claiming the control plane enforces its stated guarantees. No live provider operation was performed in this review. The prior `docs/implementation/2026-10-07-live-pipeline-proof.md` is existing evidence and was not re-executed or independently treated as live validation here.
