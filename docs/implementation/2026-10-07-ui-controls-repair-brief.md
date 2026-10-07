# UI repair + operational control integration

Work ONLY in p5n-n3t/snooze, on your existing isolated task branch. Keep the first UI commit edb56f9 and all append-only history. Merge the newest `origin/codex/snooze-command-centre` INTO your task branch (do not rebase/force-push or change the coordinator branch). No other repo writes, subagents, backend edits, automatic merges, deployment or Neon.

## First: three Important Task 2 review findings

1. `getHistory` currently downloads `/api/state` and holds all 10k rows before slicing 25. Replace it with bounded `GET /api/v2/history/events?offset=0&limit=25&q=...` returning `{entries,total,offset,limit,has_more}`. Pagination/search must request server pages, not store the full snapshot. Update the Python browser fixture to implement that endpoint. Demonstrate bounded network payload and DOM with 10k history/100 active rows.
2. Providers always renders a green credential dot and “Stored by local runtime”, but the account DTO has no credential evidence. Show Unknown/Not reported, or a neutral ownership policy; never assert per-account verified credentials from a key/label.
3. `setInterval` starts overlapping state refreshes while older fetches hang. Implement one-flight, abort/timeout and recursive settled polling with capped backoff. Retain the last true state and stale warning. Test a delayed/hanging endpoint; outstanding state fetches must remain <=1; clean up on unmount. Preserve generation-aware query timing.

## Then: Task 4 controls (backend already real)

Read `docs/implementation/2026-10-07-control-ui-contract.md` for exact endpoints/actions/revisions/receipts. Keep the existing Tokyo Nights kit-ui design, local fonts/logo and notices; no amateur raw JSON dump or new mismatched style.

Own frontend/, generated snooze/static/, UI notices and report ONLY. Extend the typed client to use `state`/`reason`/`revision` receipts (not the old future `status` stub). Show 400/409/503 rejection reasons and 202 pending truthfully. Add a bounded timeout; no optimistic fake success.

Providers: working add/edit safe account form (adapter, label, enabled, capacity, models, efforts, priority, reserve, unknown-quota policy and expiring operator quota override), save revision, test connection capability/rejection, disabled accounts keep history. Identity and real credits remain unknown unless actually reported. Never accept/render credentials or private backend stack/artifact config. LightSprint >12 requires backend evidence.

Settings: persisted interval plus concurrency/global/model limits, max two recoveries, backoff, reserve/budget/native-off policy, conservative/balanced/custom modes. Settings changes take effect without restart. Display pause/emergency persistent controls/reasons; external-managed dispatch controls disabled. Stop means no NEW dispatch/recovery, not killed remote workers.

Queue: load `/api/v2/queue` server pages, task inspection, supported draft/add/approve/hold/prioritize/retry/cancel actions. Active ownership prevents reassign/retry; cancel remains pending until actual provider acknowledgement. Reassign currently unsupported: disable with exact reason. Optional advanced task draft form may use a clearly labelled structured packet input with validation help; it is not a shell. Native use off by default, never expensive fallback.

Watch: occupied slots only with confirmed/requested separate values. Include actual cycle and durable `/api/v2/inbox` delivery receipts, inbox-only notice when no wake channel. Register a local coordinator and acknowledge selected delivery through the documented actions; acknowledgment must not resolve it. Do not claim arbitrary ChatGPT GUI wakeup. Keep usable legacy check/ack controls without misrepresenting executor ownership.

Rich analytics UI is a separate later task. Keep the bounded history/events page now; do not invent usage charts. Do not edit analytics backend.

TDD with RED tests for review bugs and operational persistence/capability/pending states, then npm test/check/build/e2e against Python. Keep generated assets clean. Verify dark/light desktop/mobile, keyboard focus, no external requests/console errors; refresh changed rendered evidence and wheel inclusion. Append report `docs/implementation/2026-10-07-ui-controls-worker-report.md`, preserve initial report, commit/push own task branch. PR creation to codex/snooze-command-centre is explicitly approved once reviewed checks pass; no need to pause asking again. Finish this whole bounded assignment.
