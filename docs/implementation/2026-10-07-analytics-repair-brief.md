# Analytics review repairs

Continue the existing isolated analytics branch; no other worker's files are yours. Merge the current coordinator branch if needed, never force-push or rebase shared history. Own the same analytics/ingest/engine/tests/docs files as the original assignment. No frontend, web, runtime, deployment, provider calls, subagents or other repositories.

Fresh review of e8e250d..247871d found two Important defects:

1. `analytics._usage_groups`: anonymous cumulative usage rows from one source collapse into `(source_id, 'cumulative', None)`. Two unrelated source-event IDs with input tokens 5 and 10 produce 10 instead of 15. Use a stable relationship identity when supplied; otherwise keep unique source events separate. Preserve deduplication of related cumulative snapshots/forks/requests. Add the regression RED, then GREEN.
2. Source provenance metadata queries all matching history facts with GROUP BY, bypassing `max_rows`. Derive metadata from the already bounded rows, or impose an explicit independent bound with honest truncation coverage. Preserve source versions/windows/cost provenance for included facts. Test a large source table with a tiny row bound; verify no uncapped fact metadata query occurs.

Run focused analytics/ingest/engine tests and integrated Python regressions. Append an exact repair report to the original worker report and push the scoped fixes. Creating a draft PR to the coordinator branch is already approved; do not pause asking for permission. Return commit IDs and evidence. Engine absence remains unavailable, never fabricate a live proof.
