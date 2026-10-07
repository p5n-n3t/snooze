# Adapter support

Adapters declare capabilities individually. A registered name, a configured account label, or a successful connection test does not mean that execution, quota, identity, cancellation or output collection is supported. Snooze keeps the capability reason visible and fails closed when an operation is unverified.

## Current capabilities

| Adapter/source | Supported behavior | Limits |
| --- | --- | --- |
| LightSprint | Read session status through an existing local MCP connection. Launch can be enabled for a configured stack, explicitly verified account, model and effort. Resume/cancel require per-account verification. | Authenticated identity and provider quota are not assumed. Reconciliation by Snooze idempotency key is unsupported. Artifact collection requires an explicit GitHub repository/path configuration. |
| Local/native, SSH, Tailscale, Ollama, v0, Figma | Registration/configuration slots only. | No verified execution adapter, model installation, remote capacity, GUI session or design-agent workflow is provided by registration. |
| External | Visible external ownership. | Does not control the external dispatcher or grant Snooze permission to claim its tasks. |
| Legacy JSON queue | Read-only import of observations/tasks for the selected project. | Importing a queue does not grant approval, execution ownership or provider identity. |
| AgentsView history API | Optional, explicit read-only GET client for inspected v1 report endpoints. | It is separate from scheduling. Missing or incompatible service/filter coverage is shown as unavailable; no engine is installed or started by Snooze. |

The LightSprint adapter reports only status, model and effort fields present in a provider response. Unknown confirmation stays null. The imported MCP key or display label is a local configuration reference, not authenticated identity. Renamed keys must be mapped through verified ownership evidence; Snooze does not match accounts by a number or label guess.

Launch is available only when backend configuration includes the existing MCP key, an explicitly approved stack ID, `launch_verified: true`, and a configured model/effort accepted for the account. The task must also be approved, in a Snooze-managed project, within policy/budget limits, and free of conflicting active scope. A launch receipt records provider task/session identity; it is not proof of saved output or completion.

Resume and cancel are enabled only when the account lists the exact operation in its verified operations. The resume message ID is persisted before the request. Cancellation stays pending and holds task ownership until the provider confirms it. Provider launch-key lookup is not verified, so timeouts and ambiguous receipts require manual reconciliation before another attempt.

## Safe public account settings

The refreshed command-centre account form, which remains in separate UI review, is limited to public policy/display settings: label, adapter, enabled state, capacity, models, efforts, priority, tools, privacy and quality classes, reserve, unknown-quota policy, quota override and cooldown. It does not accept secrets or backend routing/collection references. A connection test verifies connectivity only; it does not prove identity or successful execution.

The local `configure-provider` command is an advanced trusted configuration path. Its input file may set backend references such as `mcp_key`, `workspace_id`, `stack_id`, `launch_verified`, `verified_operations`, `verified_capacity`, `artifact_repo`, `artifact_prefix` and `artifact_credential_ref`. Those values belong in the private local state/configuration workflow, not the UI account form or a public report. The credential field is a `credential:<name>` reference; never pass the secret itself.

LightSprint capacity defaults to 12 configured reservations. It is a scheduler limit rather than a provider's confirmed slot count. The state projection contains occupied, nonterminal work only; unused capacity is not fabricated as empty worker rows. A value above 12 requires explicit adapter evidence. Quota may be unknown. Unknown quota blocks routing unless policy explicitly permits it; a manual quota override must identify its units and provenance and can expire. Snooze does not infer credit balances or reset dates from activity.

## Task and write-scope boundary

The scheduler accepts explicit, approved task packets with an input reference and SHA-256, exact scope keys, requirements, dependencies, exact output IDs/fields, and the built-in `json-records` validator. Scopes use `record:<ID>` or repository-relative `path:<path>` keys. Overlapping IDs and parent/child paths cannot be reserved simultaneously. Arbitrary validator code and task-provided shell commands are not supported.

LightSprint supplies a stack-wide sandbox. A scoped task prompt and an isolated task branch are not a hard filesystem boundary: the adapter reports `hard_write_scope` as unsupported. Require a manual diff review before applying worker output, and do not dispatch tasks whose policy requires an unavailable hard write boundary.

The collector can read only the configured GitHub repository's exact `<artifact_prefix>/<task-id>.json` file from the recorded branch. It checks the task ID, attempt ID, generation, unique exact record IDs and non-null required fields, then stores a hash and reference. This establishes structural agreement with the packet; it does not establish semantic fact accuracy. Provider idle, provider-completed status, a pushed branch or a PR receipt never substitutes for validated saved output.

## History and cost provenance

Snooze's native history uses its own durable events and normalized imported facts. It can report observed event counts, validated task outcomes, queue/run timing and other metrics only when the corresponding facts exist. Provider tokens/credits, historical eligible capacity and idle time may be unavailable. Missing values remain null with coverage/source metadata rather than becoming zero or today's account limit.

The optional AgentsView client uses a configured exact host and project mapping, reads versioned GET report endpoints, blocks redirects, and filters responses through an allowlist. Snooze never proxies arbitrary paths or mutating endpoints. Account/effort and some multi-project/model filters are not represented by every upstream endpoint; those requests fail closed as unavailable. Engine failure does not block the scheduler.

Provider/engine-reported costs and catalog/API-equivalent estimates have separate fields and sources. They do not represent subscription cash spend or savings. Subscription spend is not inferred. The aggregate usage endpoint does not expose a per-session token-coverage count, so that coverage remains unknown there.

## Delivery adapters

The durable outbox supports inbox-only delivery by default, plus an explicitly configured HTTPS webhook, a scoped loopback webhook, or an allowlisted executable invoked without a shell. Delivery IDs persist and are reused across bounded retries, so consumers should deduplicate them. Acceptance, coordinator acknowledgment and verified incident resolution are three different states.

The local MCP facade offers scoped snapshot, event, incident, task, control, register and acknowledgment tools. It uses the selected project's private token and can only read/control the project scope registered at process launch. An MCP or webhook integration does not promise to inject a prompt into an arbitrary desktop conversation; any wake behavior depends on the receiving consumer's documented support and acknowledgment.

## Future adapter rule

SSH/Tailscale workers, local/native models, Ollama, OpenCode, v0 and Figma remain roadmap or registration scaffolds until a live capability is separately implemented and verified. Do not install models, start remote services, assume hardware health, or route work based only on account labels or an advertised slot count.
