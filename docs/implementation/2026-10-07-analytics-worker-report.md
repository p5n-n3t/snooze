# Snooze analytics backend worker report

## Delivered scope

Implemented the approved Task 1/2 backend assignment on `p5n-n3t/snooze`, from `codex/snooze-command-centre` at `156c956`. The task branch was aligned with the current target branch tip `e8e250d` before the worker changes so the eventual PR contains only this worker's analytics changes.

The local report path now provides validated throughput, retry and validation-failure rates, separate queue/run latency percentiles with sample counts, recovery metrics, concurrency, timezone-aware series/heatmaps, project/account/model/tool attribution, token/cache fields and separately sourced observed/estimated costs. Spring-forward hours are explicitly marked absent; repeated fall-back hours contribute to the same local hour bucket. Unknown token/cost denominators, historical capacity coverage and idle time remain unavailable or partial instead of being presented as complete/zero.

History ingestion is bounded, replay-safe and cancellable. It persists only normalized scalar facts, deduplicates stable source event/request IDs and cumulative/fork snapshots, and advances its cursor only after a page has no rejected rows. The additive metrics migration creates the import cursor/fact tables and their indexes without rewriting existing task or observation tables.

The optional client follows the pinned AgentsView OpenAPI at commit `f4eacbc61119ebc2bfcaa47f141eb8103cf3edf1`. It checks `/api/v1/version`, validates native endpoint response shapes, filters safe fields, blocks redirects and allows only inspected GET report paths. It returns typed unavailable results for an absent engine, version/shape mismatch and filters the native API cannot represent. Scheduler, web, CLI, outbox, control, frontend and other stack repositories were not changed; no engine was installed or accessed live.

## Verification evidence

- `python3 -m unittest tests.test_analytics tests.test_history_ingest tests.test_analytics_engine tests.test_migrations -v`: 40 tests passed.
- `python3 -m unittest discover -v`: 109 tests passed, including scheduler regressions.
- The 10,000-history/100-account temporary SQLite fixture returned 10,000 events and 100 account buckets. On this run, the report measured 145.176 ms internally, 147.314 ms wall time and 147.292 ms CPU time. Process RSS high-water rose from 22.5 MiB before the report to 37.0 MiB after it. This is one local fixture measurement, not a service limit.
- The scheduler/control/web/CLI modules have no analytics or history-ingestion calls. The analytics adapter stays outside the scheduling path; the full scheduler tests passed.
- Contract fixtures verified AgentsView API version 1 and provenance normalization (`1.2.3+abc123 (API 1)`) against the native OpenAPI response shapes. No live AgentsView source was configured, so there is no live source version, imported window, or source coverage to claim. The aggregate usage endpoint does not expose a session-level token-coverage count; its token coverage therefore remains unavailable. The analytics summary endpoint's token-reporting/total-session counts are preserved.
- `pyproject.toml` declares no lint or type-check command. The complete Python unittest suite is the project's available declared verification; no frontend checks apply to this backend-only scope.
- No UI files changed, so screenshots do not apply. Backend data and request flows are attached to this task as flow-diff verification charts.

## Limits kept explicit

Snooze-side metrics describe persisted local events and imported normalized facts, not a complete provider universe. Imported usage and capacity do not have independently enumerated eligible-session/snapshot totals, so their coverage is partial. Historical utilization uses observed timestamped capacity snapshots only; idle time remains unavailable without complete ownership-window evidence. External account/effort filters and multi-value project/model filters fail closed when the AgentsView endpoint cannot apply them. A live project-scoped read, an import loop, and UI/API integration are outside this worker's ownership and remain for the coordinating work.

The changes are local and tested. Commit, push and the requested pull request are tracked separately from this report so PR creation can wait for the user decision.

## Fresh review repair report (2026-10-07)

Refreshed the branch against `origin/codex/snooze-command-centre` at `aed214946b69377a6d3f98df1056a61f97bcb9e3` by merging that target; no conflicts occurred. The merge commit is `ab54445`.

Repaired both Important findings from `docs/implementation/2026-10-07-analytics-repair-brief.md`:

1. Anonymous cumulative usage now falls back to its required stable source event ID when no usage-group/session relationship is available, so independent observations add while related snapshots and forks keep their existing deduplication identity. A regression with two anonymous cumulative rows (5 and 10 input tokens) first failed at 10, then passed at 15.
2. Source metadata is now grouped from the already bounded usage, tool-call, and capacity rows. Each source version, observed window, included-row count, and cost provenance reflects those included rows; existing fact and capacity truncation flags disclose when they are only a subset. A 100-row fixture with `max_rows=2` confirmed the report metadata covers the first two included facts and that every `history_facts` SELECT in the report path has a `LIMIT`. The prior regression exposed the uncapped grouped metadata query; it passes after the fix. Capacity snapshot version/window metadata is also retained.

Validation after repair and target merge:

- `python3 -m unittest tests.test_analytics tests.test_history_ingest tests.test_analytics_engine tests.test_migrations -v` — 42 tests passed.
- `python3 -m unittest discover -v` — 141 tests passed, including coordinator and scheduler regressions.
- The focused and full suites pass with the two new review regressions and capacity provenance assertion.

The repair changes only `snooze/analytics.py`, `tests/test_analytics.py`, `docs/ANALYTICS.md`, and this report, in addition to the required merge of the latest coordinator target. Draft PR creation was approved in the follow-up request and will be completed after pushing these repairs.
