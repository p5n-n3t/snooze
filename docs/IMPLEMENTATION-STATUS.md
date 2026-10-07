# Implementation status

**Snapshot:** coordinator source at commit `915049a` (2026-10-07). This branch contains the command-centre backend and the existing worker-watch page; the refreshed command-centre UI remains in separate review. This page separates implemented source, evidence already recorded, and release proof that is still pending. A commit or successful unit test is not by itself release readiness.

## Implemented in the current source

- A Python/SQLite runtime, private local API, existing worker-watch page, and `snooze` CLI for local open/serve, task intake, provider setup, history and optional user-service setup.
- Versioned task, attempt, event, policy, provider, artifact, history and incident records. Projects start `external-managed`; there is no automatic legacy dispatcher takeover.
- A deterministic approved-task scheduler with scope reservations, capability and quota checks, persisted bounded recovery, and structural saved-output validation. It does not use a model for routine scheduling.
- A scoped LightSprint adapter with read-only status observation. Launch requires verified backend configuration. Resume/cancel are per-account capabilities; provider launch reconciliation is not verified.
- Durable inbox delivery and a scoped stdio MCP facade, plus explicitly configured webhook/allowlisted-command delivery. The system distinguishes acceptance, coordinator acknowledgment and verified incident resolution.
- Local history reports, bounded normalized scalar import/export, and an optional separately configured read-only AgentsView client. Missing provider tokens, quota, cost, or historical capacity stay unavailable when there is no evidence.

## Evidence recorded

- [Live saved-output pipeline proof](implementation/2026-10-07-live-pipeline-proof.md): one harmless, explicitly approved LightSprint task on disposable state produced a pushed JSON envelope. Snooze collected the exact file and validated its task/attempt/generation, exact record IDs and required fields before releasing the reservation. A coordinator separately checked the arithmetic result. This does not establish general semantic accuracy or a production project handover.
- `tests/test_delivery_integration.py` exercises an abrupt process exit after incident enqueue, recovery and webhook acceptance in a second process, then a scoped MCP coordinator acknowledgment. It verifies that acknowledgment does not mark the incident resolved. This is a local integration test, not a claim that a production coordinator or remote wake channel is configured.
- Analytics worker reports record fixture coverage and one local 10,000-row/100-account measurement. No live AgentsView source was configured or queried, so no imported source version, broad history coverage, or live analytics result is claimed.
- The documentation-only worker ran `timeout 300s python3 -m unittest discover -v` on this source snapshot: 155 tests passed. Frontend, wheel, browser and release checks remain pending.

## Still pending before release

- UI review and final production asset/package verification, including the built wheel, and final desktop/mobile browser interaction evidence. The release owner must add the measured results when those checks are completed.
- Final integrated CI/test status for the release candidate. See the operator documentation worker report for checks run on its documentation-only change; that result is not a substitute for the release checks above.
- A live AgentsView connection/import and its real project mapping/coverage, if that source is intended to be part of the release. The optional client can be absent without blocking monitoring or scheduling.
- Any production executor handover. The existing Trump Files dispatcher remains externally managed until it is quiescent and active ownership is reconciled. No production ownership transfer or Neon write is part of the evidence above.
- Live capability proof for each account/model/operation before enabling launch, resume or cancellation. Configured labels and model names do not prove account identity, credits, capacity, or operation support.
- Hardware and model verification for local, SSH/Tailscale, Ollama, OpenCode, v0 or Figma workers. They remain registration scaffolds or roadmap work; no models were installed.

## Product and evidence limits

The scheduler validates output structure and exact assignment IDs; it does not claim general semantic fact validation. LightSprint task prompts and isolated branches are not a hard filesystem write boundary, so review every diff before applying it. Pause and emergency stop prevent new Snooze dispatch/recovery according to policy; they do not kill work already running remotely. Inbox/webhook/MCP delivery does not universally wake a desktop GUI or conversation. Provider/engine-reported cost, catalog estimates and subscription spend are separate; no subscription savings claim is supported.

The remaining remote fleet, design-agent, broader analytics UI and hosted deployment ideas are roadmap items, not release requirements or current capabilities.
