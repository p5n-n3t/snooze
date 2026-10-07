# Independent backend review

Review ONLY p5n-n3t/snooze branch `codex/snooze-command-centre`, newest coordinator commit, compared with `717ae2e`. Other workers own frontend and analytics. Do not edit code, other repositories, production services, global configuration, canonical data or Neon. No subagents, web searches or automatic merge. This is a bounded fresh-context review, not a redesign request.

Read the approved command-centre/control-plane specifications and plans. Focus on `tasks.py`, `providers.py`, `policy.py`, `scheduler.py`, `control.py`, `outbox.py`, `notifications.py`, `mcp_server.py`, `runtime.py`, `launch.py`, `service.py`, `queueing.py`, `artifacts.py` and `web.py`; their focused tests are evidence, not a reason to assume correctness.

Check duplicate ownership and ambiguity fencing; task/project/account scope; stale revisions and policy races; pause/emergency/recovery/cancellation semantics; persisted bounded retry/cooldown; private HTTP/MCP authentication and credential boundaries; notification acceptance versus acknowledgment versus resolution; crash recovery; safe launch/installer behavior; GitHub artifact generation and exact-ID validation. Provider idle must never become completed output. The existing live preview/Trump Files executor is external-managed.

Run `python3 -m unittest discover -s tests -q` and additional read-only reproductions if useful. Do not flag cosmetic preferences or future roadmap adapters as defects. Findings need severity, absolute/repository file path and line, concrete failure, reproduction and required repair. Mark actual unsupported operations honestly. Report exact reviewed HEAD and tests.

Your only write is `docs/implementation/2026-10-07-backend-review.md`, on your own isolated LightSprint branch; push that report, no PR/merge needed. Work until the complete review is finished. If you find no important defects, explicitly say so with the review boundaries; do not manufacture findings.
