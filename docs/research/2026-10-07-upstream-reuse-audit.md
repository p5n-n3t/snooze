# Snooze upstream reuse audit

Inspected 2026-10-07. This is a source-level research record, not a claim that these integrations are installed. Product direction: a scheduler/alarm first, historical analytics second, with selective remote delegation to save local model quota and laptop resources.

## Sources and pinned revisions

| Project | Revision inspected | License inspected | Intended use |
| --- | --- | --- | --- |
| [AgentsView](https://github.com/kenn-io/agentsview) | `f4eacbc61119ebc2bfcaa47f141eb8103cf3edf1` | Root MIT, Kenn Software LLC | Adapt selected Svelte panels; optional read-only analytics engine |
| [kit-ui](https://github.com/kenn-io/kit-ui) | `ceff715d835017daa9ec099446fa6ce71233829f` | Root Apache-2.0, Kenn Software LLC | Reuse common controls and override design tokens |
| [Paperclip](https://github.com/paperclipai/paperclip) | `228f0e2807c5b59d2aa129cf2d80b9777ebabf07` | Root MIT | Adapt durable wakeup, ownership and bounded-recovery patterns |
| [Hatchet](https://github.com/hatchet-dev/hatchet) | `9aded2376ecc6a3027ea189b54d305b038295acd` | Root MIT | Adapt due-work/execution separation and worker-availability signals |

No source from these four projects has been copied into Snooze in this research phase. Before copying code, retain the applicable license/copyright notices, pin its origin and identify modifications. Dependency and font notices are separate from the parent application's license. This audit is not a blanket clearance for every dependency or future revision.

## AgentsView: actual modules worth using

Its frontend is Svelte 5/TypeScript. The inspected package uses kit-ui, LayerChart, D3 helpers, virtual-core and a substantially larger application toolchain. Its backend is Go, with SQLite and additional optional storage/reporting systems. Snooze should not copy that entire toolchain merely to render worker rows.

All paths below are relative to [the pinned AgentsView tree](https://github.com/kenn-io/agentsview/tree/f4eacbc61119ebc2bfcaa47f141eb8103cf3edf1).

| Inspected module | Useful implementation | Adaptation boundary |
| --- | --- | --- |
| `frontend/src/lib/components/activity/ConcurrencyTimeline.svelte` | Multi-resolution activity/concurrency chart, measured tooltip positioning, report timezone handling | Replace message-derived activity with Snooze execution intervals; keep inferred activity distinct from worker heartbeats |
| `frontend/src/lib/components/analytics/Heatmap.svelte` | Compact history grid, metric selection, date drill-down and responsive cell sizing | Use Snooze outcomes/usage datasets; replace hardcoded green palette with Tokyo Nights tokens |
| `frontend/src/lib/components/usage/UsagePage.svelte` | Coordinated date/project/model filters, summary panels, attribution, cache efficiency and unsupported-usage states | Adapt panels behind a Snooze data adapter, not its entire global-store and generated-client graph |
| `frontend/src/lib/utils/liveQuery.svelte.ts` | Generation-aware query timing; superseded queries cannot settle their replacements | Reuse for truthful polling/import timing and per-panel loading state |
| `frontend/src/lib/stores/events.svelte.ts` | Shared event subscription, debounce, reconnect safety and permanent-failure handling | Wire to Snooze's event stream; retain bounded retry and polling fallback |
| `internal/usagefacts/fact.go` | Request-level usage normalization, source IDs/dedup keys, explicit cost provenance, token eligibility | Prefer consuming the engine's normalized results rather than recreating all provider parsing in Python |
| `internal/parser/codex.go` | Turn-aware `token_count` handling, task events and subagent relationships | Use optional read-only engine ingestion; never sum repeated cumulative counters as separate spend |
| `internal/activity/activity.go` and `streaming.go` | Time-range aggregation, ordered streams, cross-session usage deduplication, attribution | Valuable analytics contract; not a scheduler or a proof of useful work |
| `internal/db/analytics.go`, `usage.go`, `activityreport.go` | Project/model/time filtering and separate activity/usage accounting | Consume reporting APIs; do not open and modify the engine database directly |
| `internal/db/project_identity.go` | Project/root/remote/machine observations and immutable identity snapshots | Adapt identity principles so folder or repository renames do not split history |

`DESIGN.md` establishes a consistent control vocabulary. The app now depends on kit-ui for tables, modals, settings layout, typeaheads, date ranges, refresh controls, status indicators and typography. Its own CSS explicitly separates identity/chart tokens from common controls. This supports retheming through a coherent design system instead of one-off styling.

### Shared UI and typography

The [pinned kit-ui tree](https://github.com/kenn-io/kit-ui/tree/ceff715d835017daa9ec099446fa6ce71233829f) includes `SettingsLayout.svelte`, `Table.svelte`, `Modal.svelte`, `StatusDot.svelte`, `Typeahead.svelte`, `theme.css`, and local font assets with `fonts/OFL.txt`. Its theme contracts are CSS-variable based. Candidate fonts are Figtree for controls/body and JetBrains Mono for task IDs, numeric data and durations. Preserve font licensing if bundling them.

### What not to import wholesale

- AgentsView's desktop/Tauri shell, every provider parser, vector/embedding features, multi-database backend and localization/build graph are not prerequisites for Snooze's scheduler.
- Session analytics cannot replace task ownership, account quota checks or output validation.
- API-price equivalents are not subscription credit balances or actual cash savings.
- Full transcript archiving is opt-in, local and project-scoped; aggregate usage import must not silently collect every private conversation.

## Scheduling projects: concrete findings

The read-only research worker inspected the following pinned source files and complete root licenses. Applicability to Python/SQLite Snooze is an architectural inference, not an existing drop-in integration.

- [Paperclip `heartbeat.ts`](https://github.com/paperclipai/paperclip/blob/228f0e2807c5b59d2aa129cf2d80b9777ebabf07/server/src/services/heartbeat.ts): `enqueueWakeup` persists a wake request and execution context. Carry forward durable request identity, due time and reason. The inspected file is over 30,000 lines and tightly coupled to Paperclip's database/runtime; do not transplant that service.
- [Paperclip `recovery/service.ts`](https://github.com/paperclipai/paperclip/blob/228f0e2807c5b59d2aa129cf2d80b9777ebabf07/server/src/services/recovery/service.ts): bounded retry accounting and issue/assignee guards. Carry forward persisted attempts, budget exhaustion and conditional ownership checks before scheduling continuation.
- [Hatchet `process_sleeps.go`](https://github.com/hatchet-dev/hatchet/blob/9aded2376ecc6a3027ea189b54d305b038295acd/internal/services/controllers/task/process_sleeps.go) and [retry controller](https://github.com/hatchet-dev/hatchet/blob/9aded2376ecc6a3027ea189b54d305b038295acd/internal/services/controllers/task/process_retry_queue_items.go): separate persisted due-work selection from execution and follow-on events. Adapt the boundary rather than introducing Hatchet's distributed service stack.
- [Hatchet `worker_notify.go`](https://github.com/hatchet-dev/hatchet/blob/9aded2376ecc6a3027ea189b54d305b038295acd/internal/services/dispatcher/worker_notify.go): best-effort availability notification reduces dispatch latency. Snooze's durable periodic scan must recover a missed signal.

Neither inspected scheduler provides universal injection into arbitrary desktop chats. Wakeups target configured runtimes/adapters. Snooze needs a documented bridge, a user-configured command/API, or a durable inbox consumed on the coordinator's next turn. Delivery and acknowledgment must be reported separately.

## Recommended combination

Keep one small Python/SQLite control-plane owner. Adapt AgentsView's Svelte controls, chart panels and event-store patterns; use kit-ui consistently. Add an optional, separately configured AgentsView engine accessed through a read-only adapter for broad historical session/usage import. The engine may maintain its own private index; no SQLite read-only launch flag is assumed. Its inspected `openapi.yaml` exposes usage summaries/top sessions, analytics summary/heatmap/hour-of-week/projects/tools, activity reports and session drill-downs. Allowlist those reads rather than proxying arbitrary mutating API paths. Port scheduling invariants from Paperclip/Hatchet into focused Snooze modules with tests, without deploying their full services.

This preserves current legacy queue/account binding while making the user-facing scheduler substantially richer. It avoids loading a Node development server, a second dispatcher or a distributed database stack during normal dashboard use. Frontend build dependencies are development-time only.

Alternatives considered: a full AgentsView fork would require moving Snooze's existing provider and scheduler work into its Go application; adopting a full orchestration platform would introduce a larger runtime/integration footprint. These are possible later, but neither is the quickest targeted upgrade to this installation.
