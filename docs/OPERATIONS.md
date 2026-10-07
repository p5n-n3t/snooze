# Operations

Snooze is a local service with a browser dashboard. The browser talks to the service on localhost; opening the packaged HTML file directly bypasses the API and does not work.

## Install and open one project

Use a distinct absolute state directory for every repository. The state holds its stable project ID, SQLite history, control token, and any private credential references.

```bash
git clone https://github.com/p5n-n3t/snooze.git
cd snooze
bash install.sh --repo /absolute/path/to/project --state "$HOME/.local/state/snooze/project-one" --open
```

The installer requires Python 3.11+, creates a virtual environment beside the checkout by default, installs the `snooze` launcher into `~/.local/bin`, and initializes only a state directory without an existing `project.json`. It does not require sudo or a Node service. Optional `--queue /absolute/path/to/queue.json` imports the legacy queue as read-only input; the source queue file is not rewritten. `--service` opts into creating and starting a Linux user service; it is not required for a foreground or on-demand install.

Open the same project later with:

```bash
snooze --state "$HOME/.local/state/snooze/project-one" open
```

With no command, `snooze` opens the state selected by `SNOOZE_STATE`, the launcher binding, the compatibility state when present, or the default state. Put global `--state` before the command. `open` reuses a compatible service for the selected project, starts the registered user service or a daemon when needed, and prints `http://127.0.0.1:8765/` by default. It will not replace an unrelated listener or reinitialize an existing project.

Use `snooze --state /absolute/state serve` to run the service in the foreground. Stop that process with Ctrl-C. If you opted into a user service, use `systemctl --user status snooze.service` and `systemctl --user stop snooze.service`. Do not start two service processes for the same state; the daemon lock enforces one owner.

## Project identity and state

`init` creates a stable random project ID in `project.json`. Snooze also records the folder identity and can store explicit aliases. It does not merge repositories because their folder names match and does not automatically rename or merge project history. Keep the same state directory when a project folder moves or changes name. Do not run `init` over an existing state; it refuses to overwrite the binding. Any migration or alias change should be explicit and backed up first.

State includes private task history and a bearer control token. Keep the directory private and out of source control. The browser uses an HttpOnly, SameSite=Strict cookie and same-origin API requests. Private read APIs and mutations require the local session; the CLI token path also requires the expected Origin on HTTP requests. Never put the control token or provider credentials in a URL, public report, task, or log.

## CLI reference

Run commands with the selected state before the command:

```bash
snooze --state /absolute/state status
snooze --state /absolute/state incidents
snooze --state /absolute/state check
snooze --state /absolute/state config
snooze --state /absolute/state open
```

`status` prints a local snapshot, `incidents` lists the durable incident inbox, `check` performs one bounded check when no daemon owns the state, and `config` prints the project configuration. Use the running dashboard's Check now action while its service owns the state. `init --repo PATH` is only for a new state. `serve --port PORT` runs in the foreground; `open --port PORT` uses the existing or registered daemon. `install-service` is opt-in and refuses to overwrite an existing service unit.

## Safe provider configuration

The refreshed command-centre provider form is still in separate UI review. When available, it is limited to public account settings: label, adapter, enabled state, configured capacity, models, efforts, priority, tools, privacy and quality classes, reserves, quota policy/override, and cooldown. It does not accept raw credentials, MCP HTTP headers, stack IDs, artifact repository settings, or private credential-file paths.

Advanced backend configuration currently uses the local CLI command `configure-provider --id ID --file FILE`. Its JSON may include private references and verified backend capability fields. For example:

```json
{
  "mcp_key": "an-existing-local-mcp-server-key",
  "stack_id": "an-explicitly-approved-stack-id",
  "launch_verified": false,
  "verified_operations": [],
  "artifact_repo": "example-org/example-project",
  "artifact_prefix": "snooze-results",
  "artifact_credential_ref": "credential:github-artifacts"
}
```

Apply a file with `snooze --state /absolute/state configure-provider --id example-account --file provider-backend.json`.

Use only a key already present in the local MCP configuration. Set `launch_verified` or list `resume`/`cancel` in `verified_operations` only after confirming those specific operations for the configured account. The backend launch path also requires a configured model and compatible effort. `artifact_repo` and `artifact_prefix` enable exact GitHub saved-file collection; a private repository may use an already provisioned `credential:<name>` reference. Never place the secret itself in this JSON. The command prints public account data, not the secret.

The normal configured LightSprint capacity is 12 reservations per account. Higher LightSprint capacity needs explicit backend evidence. Capacity is a configured ceiling, not a provider-reported slot identity. Identity and quota can remain unknown. Unknown quota prevents scheduling unless the operator explicitly allows it; a manual quota override records its source, observation time, unit and optional expiry. Expired overrides no longer count as available quota. Native/local model routing is off by default and requires a separate ceiling and reserve.

## Approved tasks and output checks

Tasks are structured packets, not arbitrary shell commands. A packet requires an ID, exact project scope, input reference and SHA-256 hash, an explicit model, output IDs and required fields, dependencies, instructions, and the `json-records` validator. Record scopes must match the output IDs. For example, replace every placeholder before use:

```json
{
  "id": "extract-example-001",
  "project_id": "<stable project ID>",
  "scope_keys": ["record:example-001"],
  "input_ref": "approved-inputs/example.csv",
  "input_hash": "<64 hexadecimal characters: SHA-256 of the exact input>",
  "requirements": {"model": "<configured model>", "effort": "low"},
  "output_contract": {"ids": ["example-001"], "fields": ["result"]},
  "validator_id": "json-records",
  "instructions": "Process only the assigned record and save the required result.",
  "dependencies": []
}
```

Add a draft by default or explicitly approve it at enqueue time:

```bash
snooze --state /absolute/state enqueue --file task.json
snooze --state /absolute/state enqueue --file task.json --approve
```

The control API's task-add action creates a draft; approval is a separate action. The updated task UI remains in review. Scheduling also requires a Snooze-managed project, an eligible verified route, enabled dispatch, satisfied dependencies and policy/budget limits. Projects begin `external-managed`, so Snooze will not launch into an existing externally owned queue. The current Trump Files dispatcher remains externally managed. Handover requires the external dispatcher to be quiescent and its active sessions reconciled; the public controls do not silently perform that handover.

For artifact collection, a configured collector looks for `<artifact_prefix>/<task-id>.json` on the launched task's branch. The JSON envelope must carry the exact `task_id`, `attempt_id`, and integer `generation`, plus `records` whose IDs and required non-null fields match the approved contract. Snooze checks that structure, exact IDs, and a content hash. This is a structural check; it does not prove that a result is semantically correct. Review the saved output and code diff before applying changes. A LightSprint stack prompt and task branch do not create a hard per-file filesystem boundary.

For the example packet above, the saved file has this shape; replace the attempt ID and values with the actual assignment and result:

```json
{
  "task_id": "extract-example-001",
  "attempt_id": "<assigned attempt ID>",
  "generation": 1,
  "records": [{"id": "example-001", "result": "<saved result>"}]
}
```

One executor owns each active scope. Snooze rejects overlapping record IDs and parent/child repository paths. A launch timeout or missing receipt is ambiguous and does not authorize a second launch. Reconcile the provider task and saved artifact before retrying; provider lookup by Snooze idempotency key is not verified. Late artifacts from an older attempt are retained as quarantined evidence.

## Pause, emergency stop and cancellation

The control API's dispatch-pause setting blocks automatic new attempts and resumptions while observation and output validation continue. A manual retry can use an explicit one-time pause override; it still obeys approval, ownership, budget and concurrency checks. Emergency stop blocks new dispatch and recovery, including manual retry, until cleared. Neither control kills an already running provider session.

The default policy is paused, with a 300-second observation interval (minimum 30 seconds), project concurrency 12, global concurrency 24, at most two recovery attempts, and a 60-second base backoff. Operators can adjust supported policy values. These are policy ceilings, not a promise that every account has that many available workers. The service reports completed checks and actual cadence; slow providers can make a cycle take longer than the configured interval.

Cancellation is available only when the selected adapter advertises verified support and Snooze owns the project. A request enters `cancel_pending`; its scope remains reserved until provider cancellation is observed or ownership is explicitly reconciled. Reassignment is currently rejected. A stale observation or expired lease alone never releases ownership.

For an external-managed project, Snooze cannot pause or stop the external dispatcher. The emergency stop is not a process shutdown command. Stop the local foreground service or its configured Linux user service separately when needed.

## Incidents and coordinator delivery

Incidents and delivery requests are durable in SQLite. With no delivery channel, the inbox is the destination. Optional configured channels are an HTTPS webhook, an explicitly scoped loopback webhook, or an allowlisted absolute executable invoked with an argument array (no shell). Public controls do not accept raw webhook secrets or arbitrary commands.

Webhook delivery is at-least-once. Each request has a durable `delivery_id`; retries reuse that ID, and receivers should deduplicate it. A successful HTTP response means **accepted**, not consumed. A registered coordinator acknowledges a specific delivery through the MCP/API control action. Acknowledgment is separate from verified incident resolution. A 200/204 response, empty inbox view, provider idle state, or lack of a new error does not prove a task is complete or an incident resolved.

The scoped stdio MCP facade is available to coordinators that can launch an MCP process. In a Codex-style TOML configuration, use an absolute executable path and the selected state:

```toml
[mcp_servers.snooze]
command = "/absolute/path/to/snooze"
args = ["--state", "/absolute/path/to/project-state", "mcp"]
```

The process reads its token from the private state directory; do not copy it into the coordinator configuration. Available tools cover snapshots, events, incidents, tasks, task detail, supported controls, coordinator registration and delivery acknowledgment. Project scope is fixed when the facade starts. This MCP interface does not wake every desktop conversation or arbitrary GUI agent. A webhook or command only proves endpoint acceptance; use a documented consumer acknowledgment to prove it was read.

## History, export and import

Export local Snooze history as JSON or CSV. The range uses UTC timestamps; the timezone controls calendar grouping:

```bash
snooze --state /absolute/state history --format json --from-utc 2026-10-01T00:00:00Z --to-utc 2026-10-08T00:00:00Z --timezone America/Los_Angeles > history.json
```

The optional AgentsView source must be explicitly configured with `configure-engine --url`, an exact `--allow-host`, and an explicit `--project-mapping`. A private source may use `--credential-ref credential:<name>`; tokens are sent as backend bearer headers and are never part of a report. HTTPS is required except for an explicitly approved loopback origin. Redirects are blocked. Configuration reports that a restart is required. `test-engine` performs a read-only contract check. Unsupported filters or an absent/incompatible source return an unavailable result. Engine failure is isolated from monitoring and scheduling.

`history` exports Snooze's local event/history report. Imported provider tokens or costs appear only when source facts actually contain them. Missing token counts and quota/credit balances remain unavailable, not zero. Provider/engine-reported cost is separate from catalog-estimated cost; neither represents subscription cash spend or savings. Native execution events are evidence about Snooze's own work, not a complete inventory of every provider session.

`import-history` accepts one JSON array page of at most 1,000 normalized scalar rows (the CLI file limit is 1 MiB):

```bash
snooze --state /absolute/state import-history --file normalized-page.json --source agentsview-prod --cursor next-page-token
```

Each row needs a stable `event_id`/`source_event_id`, an existing project ID or explicit alias, a supported fact kind and timestamp. Use the same source ID across pages; stable source event IDs make retries idempotent. Only allowlisted scalar usage/activity/task/session facts persist. Prompts, transcripts, headers and unknown fields are discarded. The durable cursor advances only after a complete page has no rejected rows. Fix rejected rows and replay the page before continuing; accepted rows can safely be replayed.

## Troubleshooting

- If `open` reports an incompatible listener or wrong project, check the configured port and stop only the service you own. Snooze refuses to replace an unknown listener.
- If a task remains queued, inspect approval, executor ownership, account health/capability, model/effort, quota policy, dependencies, pause/emergency settings and concurrency reasons.
- If a task is ambiguous or cancellation is pending, preserve its scope and reconcile the exact provider task/session before retrying or releasing it.
- If History shows unavailable values, inspect the source/coverage fields. Do not substitute zero or current account capacity for missing evidence.
- Keep local `project.json`, control token, credentials, provider prompts and account labels private. Public examples and reports should use generic values.
