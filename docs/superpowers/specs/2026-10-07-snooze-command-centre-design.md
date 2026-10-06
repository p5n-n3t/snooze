# Snooze command centre: scheduler-first redesign

Date: 2026-10-07. Status: written specification awaiting user review. The user approved the recommended architectural approach in chat; this document is the next review artifact, not an implementation claim.

This supersedes the preview's proposed UI/control architecture. Existing observations, queue history, account binding and running services remain intact until the replacement has passed migration and live-adapter verification.

## 1. Intent and success

Snooze is an open-source scheduler and alarm for distributed AI work. It keeps useful, approved work moving, makes failures visible and recoverable, and saves the local coordinator's AI quota and laptop resources through selective delegation. Rich project/folder analytics are secondary: they help explain performance and tune routing without replacing task management.

JQ's requested experience: a polished web dashboard, Tokyo Nights dark/light themes, a Snooze logo, account/slot/model controls, task intervention, project history, measured token usage and a credible way to alert the coordinating agent. Trump Files is the first monitored project, not part of Snooze's product name.

Success is not a full-looking worker grid. Success is validated outputs with no overlapping assignments, bounded recovery, visible budget limits, real delivery receipts and controls that work. A healthy empty queue should leave workers idle without manufacturing new work.

## 2. Architecture selected

One Python daemon owns monitoring, durable task leases, scheduling and incident delivery. SQLite holds append-only events plus derived state. A production-built Svelte interface is served by the same localhost daemon: no permanent Node development process or heavyweight orchestration stack.

Reuse selected AgentsView panels and kit-ui controls with provenance; do not rewrite their entire design system. The optional AgentsView analytics engine supplies normalized session/usage history through a read-only API adapter. AgentsView owns its private index; “read-only” describes Snooze's access, not an assumed SQLite-server launch flag. Snooze's own execution/task events remain its scheduling source of truth. If the analytics engine is absent or unavailable, watching, dispatch and intervention continue working.

Adapters implement a common capability contract. LightSprint is the first live adapter; local registration, SSH/Tailscale and future Ollama/design providers use the same registry but remain explicitly unsupported for operations not yet implemented. No fabricated quota, identity, remote capacity or model quality.

See [the source audit](../../research/2026-10-07-upstream-reuse-audit.md) for pinned modules and reuse boundaries.

## 3. Runtime ownership and migration

The current Trump Files supervisor already dispatches work. Snooze must not become a second independent dispatcher.

- Import legacy history read-only; mark it with source and import timestamp.
- Run the new scheduler in shadow mode first: it records proposed decisions but makes no provider mutations.
- A per-project executor owner controls all task claims. Projects are `external-managed` until an explicit handover quiesces the legacy dispatcher and reconciles active sessions.
- Already-running sessions retain their provider/account/session identity and cannot be redispatched just because local state was stale.
- Preserve the current state directory through migration. Public names stay Snooze; a legacy internal directory name is not a new project or product name.
- Migration makes a SQLite-consistent backup, runs versioned additive changes transactionally and records an import cursor. Original queue files are never truncated or rewritten.
- Failure leaves the old service and history usable. No live Neon/database writes or GitHub repository rename are part of this redesign.

## 4. Interface and visual system

Navigation: Watch, Queue, Providers, History, Settings. Persistent project selector, connection state, next actual check, notification badge and theme toggle. A visible pause control and emergency stop never disappear behind settings.

### Watch

Main area: compact fleet summary, occupied slots grouped by provider/account, an execution timeline and a failure inbox. An intervention drawer opens from a worker or task without losing the selected project or filters.

Each occupied row shows logical slot, account identity label, confirmed model/effort, requested model/effort when different or unknown, short task, start time, elapsed time, last successful observation and provider state. Task state and output-validation state are separate. Provider task links are available only when verified. Empty rows are hidden; each account header still shows occupied/configured/eligible capacity.

Completed sessions move to history rather than occupying the live table forever. Filters can reveal terminal sessions. Stale/unavailable observations have timestamps and explanations, not fake failures. Available-but-unused capacity has a reason such as queue empty, dependency blocked, quota reserve or no suitable model.

### Queue and intervention

Search/filter tasks by project, status, account, model and outcome. Inspect full instructions, assignment scope, attempts, output references, validation results and event history. Controls: prioritize, hold, approve, resume, retry, request cancellation and reassign where the adapter supports them.

Every mutation displays what it affects and reports accepted, rejected, pending or confirmed—not an optimistic success label. Cancellation remains pending until acknowledgment or explicit reconciliation. Moving work requires releasing or reconciling the original owner. Manual intervention follows the same budget, scope and lease checks as automation.

### Providers

Add/edit/disable accounts and adapters without editing product source. Import named MCP connection references from local configuration; do not overwrite Codex's global configuration. New secrets are stored only in a private backend credential file, never echoed to the UI, logs or public exports.

Configure account labels, enabled state, concurrency, models/efforts, task capabilities, priority, budget reserve, quota source and cooldown. Test connection/identity separately from execution. Unknown quota is explicit; a manual operator override records source, time and optional expiration. Reported credits do not get inferred from elapsed time or token counts.

Capacity defaults to 12 for the current LightSprint setup. A different limit is a user configuration constrained by adapter evidence, not a hardcoded universal rule. Unknown higher provider limits cannot be assumed. Removed/depleted accounts stop new dispatch but keep their history visible. Current depleted-account reports are not refreshed by guessing a reset date.

### Visual direction

- Dark: ink/navy surfaces around `#1a1b26` and `#24283b`; restrained cyan `#7dcfff`, periwinkle `#7aa2f7`, violet `#bb9af7`, pink `#f7768e` accents.
- Light: warm-white/lilac surfaces with darker accessible cyan/violet/pink inks; not a blind inversion of dark colors.
- Figtree for interface/body, JetBrains Mono for technical identifiers and tabular values, self-hosted with font notices. The generated Snooze wordmark supplies brand personality.
- A coherent token system for surfaces, spacing, type, focus, borders, status and charts; consistent kit-ui tables, forms, menus and dialogs.
- Sleepy/funky personality in branding and small details; calm, precise data surfaces. No glow behind text, decorative gradients across charts or color-only status meanings.
- Keyboard navigation, explicit focus, reduced motion, contrast checks and responsive drawer/table behaviour. Long task text cannot stretch the layout.

Logo concept: [PNG asset](../../assets/snooze-logo-concept-v1.png). This is a transparent raster concept, not a claimed editable vector master.

## 5. Task and observation model

Persist stable project IDs independently of folder names. Record explicit folder aliases, normalized Git remote identity and worktree relationships; do not merge unrelated projects merely because names match. Historic events retain the identity observed at that time.

Core entities: projects, provider connections/accounts, capability snapshots, tasks, exclusive assignment scopes, attempts, sessions, leases, observations, immutable events, validation results, usage facts, incidents, delivery requests and settings revisions. Derived dashboards are rebuildable from durable data; original provider responses are reduced to a safe field allowlist.

Task progression: draft → approved → queued → reserved → starting → running → awaiting output → validating → complete. Holds, exhausted retries, cancellation and unresolved outcomes remain explicit. Provider idle/failed/completed is an observation about execution, not a task's terminal result.

Each task specifies input reference/hash, exact IDs or write scope, allowed adapter/model/effort classes, required tools/privacy constraints, dependencies, expected output and an allowlisted validator. Project approval can cover a bounded imported batch; it cannot authorize invented new batches. Imported legacy tasks are not automatically approved for mutation.

Attempts have unique idempotency keys and fencing generations. Reject overlapping active scopes within a project, not just duplicate task IDs. Late artifacts from obsolete attempts are retained/quarantined for review rather than silently merged.

## 6. Scheduling and selective delegation

The scheduling loop is deterministic and does not call a model on every heartbeat. The coordinator plans work and sets requirements; Snooze routes those approved tasks.

1. Reconcile observations, task leases and newly saved artifacts.
2. Validate outputs before declaring completion or opening replacement assignments.
3. Select due tasks with satisfied dependencies and no conflicting scope.
4. Filter workers by enabled/healthy state, verified ownership, required tools, privacy, model-quality class, quota reserve and remaining capacity.
5. Rank eligible routes by configured preference, budget headroom and measured task-class latency/success. Use neutral priors until enough comparable validated results exist; never invent precision from a few runs.
6. Transactionally reserve a task/slot with an idempotency key and lease. Launch through its supported adapter outside the transaction, then reconcile the receipt.
7. Record why each decision occurred; replenish eligible slots when work completes, without polling every idle slot with an AI prompt.

Native/local model use is off by default for bulk tasks and may be enabled with its own ceiling/reserve. Remote workers receive repetitive work only when they meet the task's quality requirements. Creative or ambiguous decisions stay with the designated coordinator/reviewer. No routing based only on “free” or number of slots.

A timeout during launch is ambiguous: reconcile provider task identity before retrying. Do not interpret it as permission to duplicate execution. Expired leases are not enough to reassign while a provider session may still be running. Require confirmed inactivity/cancellation or a bounded manual ownership resolution.

Transient errors use bounded backoff with jitter; default maximum two recovery attempts. Auth failures, unsupported operations, validation failures and exhausted budgets have distinct blocked/escalation outcomes. Per-account circuit breakers isolate failures without halting healthy providers. Successful refresh/test or an operator action can reopen a circuit.

## 7. Controls and policy persistence

Settings are validated, versioned and take effect without restarting the app. Dry-run decision previews explain impact before increasing dispatch/cost scope.

| Control | Semantics |
| --- | --- |
| Observation interval | Default 300 s, minimum 30 s; show actual cycle time and lateness |
| Request concurrency/timeouts | Bound monitoring I/O separately from AI worker slots; slow providers do not serialize the whole fleet |
| Project/global concurrency | Upper bounds after account/model/budget constraints, not target worker counts |
| Pause dispatch | Prevent automatic new attempts and resumptions; continue observation/validation. A manual dispatch requires an explicit one-off pause override and still obeys budgets/leases |
| Emergency stop | Persist dispatch stop immediately, including manual dispatch until cleared; optional supported cancellation is a separate confirmed action |
| Conservative/balanced/custom | Explainable presets for limits/cooldowns/reserves, never automatic promotion to expensive models |
| Retry/backoff/stall thresholds | Persist due times and retry counters across restart; distinguish no output progress from provider inactivity |
| Budget/quota reserve | Per project/account/model, units and provenance explicit; unknown values cannot masquerade as confirmed balance |
| Retention/import roots | Project-scoped history, log roots and aggregate-only versus transcript import choice |
| Coordinator delivery | Channel, destination reference, cooldown, escalation and test receipt |

Poll cadence is not a guarantee of response every five minutes; expose actual completed checks, overdue state and next due time. The backend reads changed settings safely each cycle and wakes promptly for supported availability signals.

## 8. Alarms and coordinator communication

An incident creates a durable outbox request carrying project/task/account/session, evidence timestamp, last action and suggested next step. Deduplicate recurring incidents; record retries, delivery receipt and coordinator acknowledgment separately. Acknowledging is not resolving. Resolution follows verified state change.

Supported launchable integration surfaces in this release: authenticated local HTTP/CLI plus a small MCP facade for coordinators that can consume it. Register a coordinator ID and permitted project scope. The durable inbox works even if no active coordinator is connected.

Optional user-configured HTTPS webhook or allowlisted executable adapter can deliver wakeups. No `shell=True`, arbitrary commands from task text or credentials inside incident payloads. A test incident must prove endpoint acceptance; acknowledgment must prove the coordinator consumed it. If the destination lacks a documented wake API, the UI says “inbox only,” not “coordinator notified.”

Product-specific chat wakeup/automation is enabled only after its supported mechanism is configured and tested. Snooze cannot universally inject a prompt into an arbitrary desktop conversation. Monitoring and recovery remain persistent when this chat ends; further reasoning depends on an actual registered runtime/channel.

Quiet when healthy and unchanged. Notify on actionable failure, completion, exhausted recovery/budget or required user decision. Configurable summaries are separate from incident delivery and do not spend AI quota unless explicitly requested.

## 9. Historical analytics

Global date/project/folder/account/model/effort filters with links to sessions and task attempts. Calendar boundaries respect the selected timezone; stored timestamps remain UTC. Repeated/forked cumulative usage is deduplicated before totals.

Required panels:

- Task outcomes, validated throughput, retry/validation-failure rates and time to recovery.
- Execution/concurrency timeline, busy/idle time, queue latency and run-duration p50/p95 with sample counts.
- Calendar/day/hour-of-week activity heatmaps and project/folder breakdowns.
- Token input/output/reasoning/cache categories where actually observed, cache efficiency and usage coverage.
- Provider/model attribution, cost trend, highest-usage sessions and tool-call breakdown where imported evidence supports them.
- Attempt/event drill-down, full assigned prompt, artifact/branch references and root/subagent relationships when IDs prove them.
- CSV/JSON export of the selected range, excluding credentials and raw private transcripts by default.

Every metric has units, source, time window, sample/coverage count and known missingness. Unavailable token/credit fields are null and labeled unavailable, not zero. Provider-reported cost and catalog/API-equivalent estimates remain separate; subscription cash savings are never invented. Estimated model-price snapshots must identify version/as-of source.

Historical utilization uses the eligible-capacity snapshot for that time window; missing capacity history is not filled with today's account limits. Message-derived activity is a proxy distinct from worker execution/heartbeat duration. Completion means a validated task outcome, not a provider idle event.

Import is incremental, cancellable and bounded: project-scoped local log roots, read-only engine APIs, durable cursors, bounded batch sizes and no AI calls. Full transcript capture requires explicit opt-in. Analytics can be disabled or fail without stopping task scheduling.

The inspected engine contract includes GET `/api/v1/usage/summary`, `/api/v1/usage/top-sessions`, `/api/v1/analytics/summary`, `/api/v1/analytics/heatmap`, `/api/v1/analytics/hour-of-week`, `/api/v1/analytics/projects`, `/api/v1/analytics/tools`, `/api/v1/activity/report`, and session usage/children/tool-call drill-downs. The adapter checks the configured engine's contract/version and translates responses into Snooze DTOs. It never forwards arbitrary paths or mutating endpoints such as session deletion, publishing or resume. Unsupported/mismatched responses produce an explicit unavailable panel, not invented values.

## 10. Security, resource and deployment boundaries

Localhost is the default. Retain host/origin checks, authenticated mutations, restrictive CSP, escaped content and safe links. Protect read APIs containing private task history too. New configurations/exports never expose bearer tokens or authorization headers.

Provider endpoints and webhook destinations are explicitly approved connection settings. Validate destination schemes/hosts, redirects and credential references. Local/Tailscale endpoints require an explicit network scope; do not turn provider settings into arbitrary network probing.

Filesystem roots and executable hooks are allowlisted local configuration. Tasks cannot set arbitrary commands, Git commands or validator code. Account disablement does not delete history. Destructive operations need separate explicit confirmation. No automatic model installation, VM provisioning, GUI login or API-key selection.

Keep monitoring concurrency bounded and analytics off the critical loop. Serve production static assets, lazy-load history panels, paginate large tables and debounce live events. Test a representative 100-worker/10,000-history fixture; report measured CPU/RAM/request latency rather than promising unmeasured limits. Current service limits are preserved until measurements justify a change.

Remote hosting is a later explicit deployment choice with authentication/TLS/network restrictions—not changing the bind address to expose the current local cookie/token scheme. SSH/Ollama/v0/Figma registration slots are capability-aware scaffolding until a live adapter is verified.

## 11. Launch experience

The user should type `snooze` or `snooze open`. It opens an existing compatible daemon; otherwise it starts the configured service and opens the confirmed URL. No second daemon, overwritten project config or raw-file preview. A first run presents project setup. Foreground serving remains available for developers.

The installer checks Python/venv prerequisites, installs the production frontend/package into a project-owned environment and optionally configures the user service. No silent global Node/system changes. Development builds may require Node; normal installed use does not.

Today, before this redesign is implemented, the verified running URL is `http://127.0.0.1:8765/`. The existing user service is `snooze.service`; `systemctl --user start snooze.service` starts it if stopped. The new shorthand commands above do not exist yet.

## 12. Delivery sequence and acceptance

The written implementation plan must split work into disjoint modules and checkpoint each phase. Prefer remote/cheap workers for bounded implementation; do not inherit the coordinator's expensive model/effort silently. Keep the existing service usable during development.

Acceptance gates:

1. **Polished interface and launch:** real production build; dark/light and keyboard/reduced-motion checks; no console errors; occupied rows, drawers and settings work against real backend data; opening an existing daemon is idempotent.
2. **Durable control plane:** transactional claims, overlapping-scope prevention, late-output fencing, ambiguous-launch reconciliation, bounded retries, settings revisions and restart recovery tested with fake adapters.
3. **Live capability proof:** one real LightSprint observation and one approved bounded recovery/dispatch with receipt, saved output and validation. Unsupported controls are disabled with reasons. Quota/identity limitations remain explicit.
4. **No competing scheduler:** legacy external-managed mode verified; handover tested before automatic dispatch is enabled for an existing project.
5. **Coordinator proof:** test incident persists across restart, produces a real delivery receipt where configured and is acknowledged by a registered coordinator; missing wake support is honestly displayed.
6. **Analytics proof:** fixtures for token dedup, missing usage, timezone boundaries, cost provenance, source/fork attribution and historical capacity; live read-only project import or an explicit unavailable state. Watch remains operational without the optional engine.
7. **Release:** installer and unit/browser tests, migration/rollback and troubleshooting docs, copied-module/license inventory, no secrets/private queues in Git, honest GitHub description/topics/badges and measured resource report.

This redesign is not complete merely because a mockup, commit or build exists. Scheduling, adapter receipt, artifact validation, coordinator delivery and analytics import require separate evidence.
