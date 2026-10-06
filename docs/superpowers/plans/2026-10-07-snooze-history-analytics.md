# Snooze Historical Analytics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deep project/folder/time/model history and measured usage analytics while keeping scheduling responsive and truthfully showing missing evidence.

**Architecture:** Snooze aggregates its durable execution/task events. A separately configured read-only AgentsView API adapter supplies wider session/token/tool history; its private index is owned by AgentsView. Adapt selected AgentsView chart panels into the Svelte History workspace behind Snooze DTOs; never port every provider parser or introduce another dispatcher.

**Tech Stack:** Python 3.11+/SQLite, API response validation/caching, Svelte 5, LayerChart/D3, pinned upstream Svelte modules; unittest, Vitest and Playwright.

**Spec:** `docs/superpowers/specs/2026-10-07-snooze-command-centre-design.md`.

## Global Constraints

- UTC storage, selected-timezone calendar boundaries, explicit observed/estimated/unavailable values and sample/coverage counts.
- Unknown tokens/credits are null, not zero. API-equivalent estimated cost is separate from provider-reported cost and subscription cash spend.
- Project IDs survive explicit path/remote aliases; identical basenames are not merged automatically.
- Import is scoped, read-only, bounded, cancellable and incremental; full transcripts are opt-in. No AI calls to aggregate reports.
- Optional engine failure cannot stop monitoring or scheduling. Never proxy arbitrary/mutating engine API paths.
- Preserve pinned AgentsView/kit-ui source, dependency and font notices; no whole-platform fork/runtime requirement.
- Exports exclude credentials/private transcripts by default. No external font/data requests from the UI.

## Review Focus

- Repeated cumulative usage, forks and subagent relationships must not double-count token spend: Task 1/2.
- Missing usage must remain visibly incomplete instead of becoming zero cost: Task 1/3.
- Midnight/DST boundaries and explicit folder renames must not shift or split project totals: Task 1.
- Current account capacity cannot be substituted into historical utilization windows: Task 1.
- Broken/unavailable/incompatible engine responses must leave Watch/dispatch usable: Task 2/3.

## Shared types and files

`HistoryFilter(project_ids, from_utc, to_utc, timezone, accounts, models, efforts)` lives in `snooze/analytics.py`. `history_report(filter: HistoryFilter) -> dict` returns `summary`, `series`, `heatmap`, `breakdowns`, `top_sessions`, `coverage`, `sources` and measured `query_ms`. Each metric carries value/unit/source/coverage; absent data remains null.

`EngineClient.query(report_kind: str, filter: HistoryFilter) -> EngineReport` allowlists paths/parameters and validates required response shapes. Define `EngineReport(state, payload, source_version, source_window, coverage, error_kind)` in `analytics_engine.py`, with payload already normalized to the report contract above. `ImportReceipt(source_id, cursor, accepted, duplicates, rejected, cancelled)` is defined in `history_ingest.py`. Engine DTOs are converted before exposing them publicly; no raw headers/private payload pass-through. Engine pricing/usage provenance is retained.

## Task 1: Event history, project identity and honest metrics

**Files:** Create `snooze/{analytics,history_ingest}.py`, `tests/{test_analytics,test_history_ingest}.py`; extend additive migrations for usage/capacity/import cursors and event indexes.

**Interfaces:** `ingest_events(source_id: str, cursor: str, rows: list[dict]) -> ImportReceipt`, `history_report(filter: HistoryFilter) -> dict`; consumes durable task/attempt/events from the control-plane plan, not raw legacy queue running flags.

- [ ] **Step 1: Write failing metric fixtures.** Validated outcomes define throughput; idle does not. Duplicate request IDs and repeated cumulative snapshots count once. Missing tokens remain null with coverage. p50/p95 have sample count; run duration and queue latency are separate. Unknown historical capacity yields unavailable utilization, not today's denominator.
- [ ] **Step 2: Write time/identity/import tests.** Calendar-day/hour heatmaps use selected timezone through DST and midnight boundaries. An explicit project alias retains history; unrelated same-name folders remain separate. Restart/import replay does not add duplicate events; cancellation stops between bounded batches without losing the cursor.
- [ ] **Step 3: Run `python3 -m unittest tests.test_analytics tests.test_history_ingest -v` to verify missing functions fail.** Name the null-handling test `test_missing_usage_is_null_not_zero`; it asserts the report's token metric value is `None` and usage coverage is zero for a no-usage fixture. Each metric object has `value`, `unit`, `source` and `coverage`, making this assertion independent of chart rendering.
- [ ] **Step 4: Implement indexed incremental event ingestion and bounded SQL aggregation.** Keep execution/heartbeat intervals separate from message-derived activity proxies. Store source IDs and units/provenance. Do not import raw transcripts by default or implement speculative provider token estimates.
- [ ] **Step 5: Run fixture and scheduler regression suites.** Querying a 10,000-history/100-worker fixture does not block a due scheduler tick beyond the measured baseline tolerance; report observed latency/resource numbers. Commit scoped analytics/ingest/schema changes.

## Task 2: Optional AgentsView engine adapter

**Files:** Create `snooze/analytics_engine.py`, `tests/test_analytics_engine.py`, `docs/ANALYTICS.md`; extend provider/settings DTOs for safe engine configuration.

**Interfaces:** `EngineClient.query` above; report kinds map to inspected GET endpoints: usage summary/top sessions, analytics summary/heatmap/hour-of-week/projects/tools, activity report and selected session usage/children/tool-call drill-downs.

- [ ] **Step 1: Write failing contract/security tests.** `test_absent_engine_is_unavailable` asserts `client.query("usage_summary", filters).state == "unavailable"`. Unknown path/report kind rejected; mutating session endpoints never callable. Redirects cannot escape the approved engine host/scope. Timeout, malformed JSON and contract mismatch produce typed unavailable reports. Private auth headers never reach exports/UI. Run `python3 -m unittest tests.test_analytics_engine -v`; expect missing adapter/behaviour failures before implementation.
- [ ] **Step 2: Implement read-only request/normalization with bounded timeout, filter-keyed cache and source/version metadata.** Cache replacement is not a new additive usage event; querying the same report twice must not double totals. Preserve reported-versus-estimated costs and engine dedup/relationship attribution.
- [ ] **Step 3: Add explicit engine connection/test/import configuration.** Do not install an upstream engine silently or assume a SQLite read-only serve flag. Operator configures source roots and retention in the engine; Snooze accesses its read APIs. Version/contract mismatch stays visible.
- [ ] **Step 4: Verify fixture contract coverage and, if configured, one live project-scoped read.** Record actual version, source window and response coverage. An absent engine is a verified unavailable state, not proof of broad historical ingestion. Commit adapter/tests/docs.

## Task 3: Rich History workspace and exports

**Files:** Create/adapt `frontend/src/components/history/{HistoryPage,Summary,Timeline,Heatmap,HourOfWeek,ProjectBreakdown,UsageAttribution,CostTrend,TopSessions,ToolBreakdown}.svelte`, API types/store and tests; add scoped history endpoints/export handlers to `snooze/web.py`.

**Interfaces:** Consumes `history_report`/`EngineClient` normalized reports. GET history endpoints accept `HistoryFilter`; authenticated export returns selected-range CSV/JSON with stable IDs, provenance and explicit nulls. Task/session links open the existing drawer with attempts, assigned prompt, artifacts and evidence-backed child relationships.

- [ ] **Step 1: Write UI/export tests.** Global filters remain linked across panels; missing data shows unavailable/coverage; observed cost and estimate labels never merge; report timezone is preserved. Exports omit secrets and raw transcripts. Relationships render only from actual IDs, not guessed similarities.
- [ ] **Step 2: Extract/adapt the pinned upstream panels and supporting date/format/query helpers.** Record exact origin/path/revision/modifications. Replace app-global store/i18n coupling with Snooze DTOs/shared English labels; use existing kit-ui controls and approved chart tokens. Do not duplicate an entire settings/control system.
- [ ] **Step 3: Implement outcome/throughput/latency/recovery, concurrency, heatmaps, account/model/project breakdowns, token/cache/cost/tool attribution and top-session drill-downs.** Lazy-load/paginate history; retain independent panel errors and truthful coverage. Imports run as bounded background work rather than in the scheduler's critical loop.
- [ ] **Step 4: Run `npm --prefix frontend test`, `npm --prefix frontend run check`, `npm --prefix frontend run build` and `npm --prefix frontend run e2e`; expect all pass.** Verify dark/light screenshots, responsive/keyboard/tooltip behaviour and no browser console errors. A broken optional engine leaves native event panels, Watch and dispatch controls usable. Verify exports and filter/date reload persistence against actual backend responses.
- [ ] **Step 5: Run all Python/frontend/browser suites and whole-branch review.** Test fresh installer, existing-state migration, restart, optional-engine absence and one approved live task/result/notification flow from plan 2. Commit/push scoped changes and publish measured resource/verification evidence with remaining unsupported adapters clearly labeled.

## Completion checklist across all three plans

- [ ] Production dashboard and one-command launch work; no raw-file confusion or duplicate daemon.
- [ ] Provider/account/slot/policy/task controls are functional or explicitly unsupported, with verified backend persistence.
- [ ] Approved scheduling/recovery is durable, bounded and does not overlap scopes or seize external-managed projects.
- [ ] Coordinator delivery has receipts/acknowledgments or says inbox-only; no arbitrary GUI wakeup claim.
- [ ] History/usage/filter/export tests prove source provenance, dedup, null handling and timezone/capacity correctness.
- [ ] Real provider receipt, saved artifact and validation are demonstrated separately from UI/build proof.
- [ ] Documentation, installer, attribution, GitHub metadata and resource measurements match the shipped features.
- [ ] Current Trump Files history and live Neon remain untouched by this application redesign.
