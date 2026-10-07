# Snooze analytics backend worker

Implement Tasks 1 and 2 of `docs/superpowers/plans/2026-10-07-snooze-history-analytics.md`, reading those exact requirements first plus Global Constraints. Spec sections 5/9/10 are binding. Work only on p5n-n3t/snooze from codex/snooze-command-centre, own cloud branch. Do not touch other stack repositories. If necessary clone the explicit Snooze GitHub remote; never substitute another repository.

## Scope

Own `snooze/analytics.py`, `history_ingest.py`, `analytics_engine.py`, `tests/test_analytics.py`, `test_history_ingest.py`, `test_analytics_engine.py`, `docs/ANALYTICS.md`; extend `snooze/migrations.py` additively for these metrics tables only. No edits to web/CLI/control/scheduler/views/store or frontend. Other workers own them. No subagents, merge, deploy, global config, VM/model installation, Neon writes or AI calls for aggregation. Follow TDD with meaningful fixtures, narrow commits and self-review. Keep worker report under docs/implementation/2026-10-07-analytics-worker-report.md.

Current repository interfaces: TaskRepository(path), connection(write=False) is an explicitly closed SQLite context; tasks/attempts/events schema in migrations.py; events have project/task/attempt/kind/UTC at/data/source_id/source_event_id. Attempts distinguish active ownership/released state; only `attempt_complete` with validated outcome is throughput. Scheduler emits requested/confirmed provider observation, reserved/starting/running/blocked/complete events and validation results. Core scheduling uses no metrics engine. Preserve all existing schema/history and tests.

## Contract to expose

`HistoryFilter(project_ids, from_utc, to_utc, timezone, accounts, models, efforts)` and `history_report` per plan. Provide `Analytics(repository).history_report(filter)` plus a clear module-level wrapper accepting a repository (no global singleton or hardcoded state path). Each metric `{value,unit,source,coverage}`. Summary, series, heatmap, breakdowns, top_sessions, coverage, sources, measured query_ms. Include task outcomes/validated throughput, queue/run p50/p95 + samples, retry/validation/recovery, concurrency timeline, account/model/project/tool attribution, token/cache categories and separate observed/estimated costs where source facts exist. Unknown capacity/utilization and token/cost coverage remain unavailable, not zero.

Incremental ingestion class can take repository explicitly; preserve plan's `ingest_events(source_id,cursor,rows)` method shape and ImportReceipt. Bounded batches/cancellation, durable cursor and source IDs, safe fields only, no raw transcripts. Project IDs/explicit aliases from TaskRepository never merge basenames.

EngineClient allowlists the inspected GET report kinds, no arbitrary proxy routes or redirects. Configured host/network scope required, absent engine typed unavailable, short timeouts, bounded cache keyed by all filters, contract normalization with real provenance and missingness. Read-only means Snooze's API access; don't install the engine. No raw response/auth headers in DTOs.

## Verification

Write RED tests before production: duplicate request/cumulative/fork usage, missing-null coverage, DST/midnight timezone, explicit aliases, replay/cancellation, historical capacity unknown, confirmed vs requested attribution, malformed/absent engine/redirect/security. Run focused tests GREEN and scheduler regressions; measure a 10,000-history/100-worker fixture without a heavyweight DB/AI call. Report exact evidence, versions, measured latency and unsupported panels. Commit/push Snooze-only branch and draft PR to codex/snooze-command-centre. Return branch/commits/PR/test results and blockers; do not claim broad ingestion from an absent engine.
