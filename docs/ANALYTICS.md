# Snooze analytics and history imports

The analytics module reads Snooze's durable task events and normalized history facts. It has no global state path and makes no calls to the scheduler. The optional AgentsView client is a separate read-only adapter; aggregation does not install or start that service.

## Local reports

Pass the repository and filters explicitly:

```python
from snooze.analytics import Analytics, HistoryFilter
from snooze.tasks import TaskRepository

repository = TaskRepository("/path/to/snooze.sqlite")
filters = HistoryFilter(
    project_ids=("repo:my-project",),
    from_utc="2026-10-01T00:00:00Z",
    to_utc="2026-10-08T00:00:00Z",
    timezone="America/Los_Angeles",
)
report = Analytics(repository).history_report(filters)
```

`from_utc` is inclusive and `to_utc` is exclusive. Both may be UTC timestamps, ISO datetimes, or `None`. Calendar grouping uses the selected IANA timezone; storage and comparisons remain UTC. `project_ids` match project IDs or explicit registered aliases. An unknown requested project selects no rows, and equal folder basenames never merge by themselves.

`history_report(repository, filters)` is the module-level equivalent. Reports contain `summary`, `series`, `heatmap`, `hour_of_week`, `breakdowns`, `concurrency`, `top_sessions`, `coverage`, `sources`, and measured `query_ms`. Summary metrics use this shape:

```json
{"value": null, "unit": "tokens", "source": "imported usage facts",
 "coverage": {"observed": 0, "eligible": null, "missing": null}, "state": "unavailable"}
```

An unknown denominator stays `null`; imported usage totals therefore report partial coverage while eligible source sessions are not independently enumerated. No usage is `null`, not zero. Costs stay split into provider/engine observed values and catalog/API-equivalent estimates. Different currencies or unlabeled costs do not collapse to a misleading total. Coverage describes the evidence available to Snooze; it does not claim that a source exported its complete history.

Local execution metrics come from durable event kinds. Throughput counts only `attempt_complete` events with `validation` equal to `true` or `valid`; provider idle is not success. Queue latency is task creation to reservation, while run duration is starting to validated completion; both include their sample count. Retry rate uses attempts whose generation is greater than one over the sampled attempts. Validation-failure rate uses invalid validation outcomes over attempts with a recorded valid or invalid validation result. Retries, validation failures, recovery events and recovery duration are also available as separate counts/timings. Requested and confirmed model attribution are separate as well.

Series and heatmap buckets use local calendar dates/hours. Heatmap rows keep a 24-slot `hours` array and a matching `hours_present` array; a missing spring-forward hour is marked absent, while both fall-back occurrences contribute to the same hour slot. Historical utilization uses only timestamped capacity snapshots and is marked partial because eligible snapshot coverage is unknown. Idle time remains unavailable because Snooze does not have complete ownership-window evidence. If a bounded query truncates a source, related metrics carry partial coverage; if ownership history exceeds the limit, the concurrency timeline is omitted and concurrency is unavailable rather than publishing an incorrect baseline.

## Safe incremental imports

`HistoryIngestor(repository).ingest_events(source_id, cursor, rows)` (also exported as `ingest_events(repository, ...)`) accepts normalized scalar facts for `activity`, `usage`, `tool_call`, `capacity_snapshot`, `task`, `attempt`, and `session`. It stores only the allowlisted fields in the additive `history_facts` and `history_imports` tables. Transcript, prompt, authorization, and unknown fields are discarded. Projects must already exist or have an explicit alias in `TaskRepository`.

Rows commit in bounded batches (100 by default, maximum 1,000). Stable `(source_id, source_event_id)` values make replay idempotent. A source request ID is unique within its source; cumulative snapshots group by source plus usage group/root relationship and contribute their per-field maximum, so repeated snapshots and child-fork copies are not summed as new spend. Non-cumulative request facts add once. Cost values retain currency and observed/estimated source labels.

The cursor advances only after a complete page has no rejected rows. Cancellation or an invalid row leaves the prior cursor in place; batches already stored are safe to replay. `ImportReceipt` reports accepted, duplicate, rejected and cancelled counts and the durable cursor. There is no transcript import mode in this assignment.

## Optional AgentsView source

`EngineClient` is a separately configured client for the pinned AgentsView v1 OpenAPI endpoints. It only issues `GET` requests for usage summary/top sessions, analytics summary/heatmap/hour-of-week/projects/tools, activity reports, and session usage/children/tool-call drilldowns. It reads `/api/v1/version` first and requires API version 1; `EngineReport.source_version` carries the runtime version, commit and API version. It validates endpoint-specific response shapes and strips fields outside an explicit safe-field allowlist before returning a DTO.

Configure the engine origin together with exact allowed host names. HTTPS is required except for an explicitly allowed loopback host. Redirects are blocked, responses are capped at 2 MB, timeouts default to 2 seconds (maximum 10), and successful reads are cached for 15 seconds (maximum 300) in a bounded cache keyed by report kind and every `HistoryFilter` field. Authentication is sent only as a bearer header and is never included in an `EngineReport`.

The upstream API accepts fewer filter dimensions than `HistoryFilter`: the adapter maps one project and one model where the selected endpoint supports them, plus timezone and range. Account and effort filters, multiple project/model values, and filters unsupported by a drilldown return a typed `unavailable/unsupported_filter` result without making a request. Calendar-day endpoints disclose their calendar-day granularity in `source_window`; the activity report retains an RFC3339 window. Aggregate usage totals do not include a session token-coverage count, so their token coverage is explicitly unavailable. The analytics summary reports the endpoint's token-reporting and total-session counts. Missing, invalid or incompatible engine responses never interrupt Snooze scheduling.

This backend assignment does not add web, CLI, control-plane settings, export routes, or a live engine import loop. Those integration surfaces belong to the coordinating worker; until configured, `EngineClient()` returns a typed `not_configured` result.
