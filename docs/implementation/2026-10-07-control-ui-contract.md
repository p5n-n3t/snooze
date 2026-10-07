# UI integration contract (coordinator backend)

Private reads use the existing same-origin cookie. Mutations POST `/api/v2/control` with `{action,target_id,values,expected_revision}`. The response is `{action_id,state,reason,revision,status_code}`; show confirmed/pending/rejected literally. HTTP 400 means malformed/invalid, 409 means stale revision or unsupported/ownership policy, 503 is a typed provider outage. Never convert pending into success.

## Operational pages

- `/api/v2/state`: schema-v2 snapshot including persisted policy revision, executor, actual monitor cycle and provider registry. `accounts` now includes both `id` and compatibility `server_key`. Identity and credit balances can be null. Confirmed effort stays null when not supplied by the provider.
- `/api/v2/queue?offset=0&limit=50`: `tasks,total,offset`; rows have `id,project,state,priority,revision,summary,approved`. Use bounded pages.
- `/api/v2/providers`: `accounts`, with public config and supported capability/reason pairs.
- `/api/v2/tasks/{id}`: full allowlisted instructions, scopes, attempts, events and HTTPS references.
- `/api/v2/events?after=0&limit=100`: bounded cursor feed; polling fallback, not a claimed SSE stream.
- `/api/v2/inbox`: bounded deliveries with accepted/acknowledged/resolved states and `wake_mode`. No configured channel means **inbox-only**, not automatic GUI delivery.

## Actions

- Policy: `policy-config`, target current project ID; values can include interval (30–86400 s), max_concurrent/global_concurrent, model_limits, reserve, allow_unknown_quota, max_recoveries (0–2), backoff_seconds, mode, allow_native/native_ceiling/native_reserve. Native off by default. Use current settings revision.
- `dispatch-pause` `{paused:bool}` and `emergency-stop` `{stopped:bool}` require Snooze executor capability. External-managed projects cannot pause the external dispatcher. Emergency stop blocks new dispatch/recovery; it does not assert that already-running remote processes were killed.
- `account-config`, target stable account ID: label, adapter, enabled, capacity, models, efforts, priority, tools, privacy, quality, reserve, allow_unknown_quota, quota_override `{value,unit,expires_at}` or null, cooldown_until. Existing local `mcp_key`/workspace references may be bound; never accept raw headers/tokens. Default LightSprint capacity 12; >12 requires backend evidence. Use account revision (0 when adding).
- `account-test`, target configured account ID: verifies connection only, not successful execution. An unimplemented adapter does not magically become launch-capable.
- `hold`,`approve`,`prioritize` `{priority:int}`: target task ID/current task revision; active ownership blocks assignment edits.
- `retry`/`resume` require approved inactive ownership and Snooze-managed executor; an explicit `{override_pause:true}` may bypass pause once but never emergency/budgets/leases. Active sessions must be reconciled first.
- `cancel`: only configured supported Snooze-owned active sessions, returns pending; scopes remain held until provider confirms cancellation.
- `reassign`: currently rejects with an exact unsupported reason rather than silently ignoring the requested account. Do not show a functional reassignment selector.
- `task-add`: saves a **draft** packet; supply id, scope_keys, input_ref, input_hash (SHA256), requirements with explicit model, output_contract `{ids,fields}`, validator_id `json-records`, instructions, dependencies. Record scopes must exactly match output IDs. Supplied `approved:true` is ignored; use the separate approval action. There are no task-supplied executable validators.
- `coordinator-register`: values `{coordinator_id}`, scoped to current project. `incident-ack`: target delivery ID, values `{coordinator_id}`. Acknowledgment is not resolution.

Backend-only stack, artifact collector, webhook credentials and endpoint allowlists are not public raw configuration fields. No arbitrary shell, OAuth account selection, VM/model installation, external dispatcher takeover or Neon write is triggered by these controls.
