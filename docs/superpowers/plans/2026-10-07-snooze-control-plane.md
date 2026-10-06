# Snooze Durable Control Plane Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make provider/task controls and automatic approved-queue recovery real, durable, budget-aware and safe against duplicate execution.

**Architecture:** One SQLite-backed executor owns each project; legacy projects begin external-managed. Capability-advertising adapters observe/launch/resume/cancel only supported operations. A deterministic scheduler and durable incident outbox follow Paperclip/Hatchet's ownership/recovery boundaries without deploying their services.

**Tech Stack:** Python 3.11+, SQLite transactions, standard-library HTTP/CLI, minimal MCP facade, fake adapters/clock in unittest; Svelte controls from the command-centre plan.

**Spec:** `docs/superpowers/specs/2026-10-07-snooze-command-centre-design.md`.

## Global Constraints

- Default 300 s interval, minimum 30 s; default maximum two recovery attempts. No AI calls to decide routine heartbeat actions.
- Exclusive task/write-scope ownership, idempotency keys and late-output fencing; stale observations or expired leases alone cannot authorize reassignment.
- LightSprint capacity defaults to 12; higher values require explicit configuration and adapter evidence. Quota/identity may be unknown; manual overrides have provenance/expiry.
- Local/native bulk model use is off by default; no silent fallback to expensive models. Native use needs an explicit ceiling/reserve.
- Existing Trump Files dispatch remains external-managed until an explicit tested handover. No Neon writes, original queue rewriting or automatic VM/model provisioning.
- Credentials are private backend references; settings are validated/versioned and take effect without restart.
- Preserve source/license notices for any adapted code and comply with the audit's pinned revisions.

## Review Focus

- A launch timeout followed by late provider acceptance must not create two assignments: Task 2/3.
- Different task IDs with overlapping record/write scopes must still conflict: Task 1/3.
- Account renumbering/removal, unknown quota and temporarily inaccessible providers must not guess ownership or credit balances: Task 2/3.
- Paused/emergency-stopped projects must not resume work through a recovery or manual bypass: Task 3/4.
- A successful webhook response without coordinator acknowledgment must not falsely resolve an incident: Task 5.

## Shared types and file ownership

`snooze/domain.py` defines dataclasses: `TaskSpec(id, project_id, scope_keys, input_ref, input_hash, requirements, output_contract, validator_id, approved, dependencies)`, `AccountSnapshot(id, enabled, capacity, observed_at, capabilities, models, quota, health)`, `AttemptReceipt(attempt_id, generation, idempotency_key, session_id, state)`, `CycleReport(started_at, finished_at, decisions, errors)`, `Eligibility(eligible, reasons, rank)` and `ValidationResult(state, errors, artifact_hash)`. Quota carries value/unit/source/observed-at/expiry with optional unknown values; scope keys use normalized repository-relative paths or explicit record IDs, not machine-local checkout paths. All numeric timestamps are UTC Unix seconds.

`TaskRepository` in `snooze/tasks.py` owns transactions. `Policy.evaluate(task: TaskSpec, account: AccountSnapshot, now: float) -> Eligibility` returns `eligible` plus structured reasons. `Scheduler.tick(project_id: str, now: float) -> CycleReport` consumes repositories/policy/adapters. `ProviderRegistry` never reads credentials into public DTOs. Keep scheduler, validation and notification responsibilities separate.

## Task 1: Additive migration and exclusive task ownership

**Files:** Create `snooze/{domain,migrations,tasks}.py`, `tests/{test_migrations,test_tasks}.py`; modify `snooze/store.py` only for migration/repository integration.

**Interfaces:** `migrate_state(path: Path) -> MigrationReport`; `TaskRepository.reserve(task_id: str, account_id: str, scope_keys: tuple[str,...], now: float) -> AttemptReceipt`; `release(attempt_id: str, evidence: dict) -> bool`; `record_artifact(attempt_id: str, generation: int, reference: dict) -> str` returns accepted/quarantined.

- [ ] **Step 1: Write failing migration/claim tests.** A SQLite-consistent backup retains jobs/observations/incidents; repeated migration is idempotent; rollback on failure leaves old data usable. Two concurrent tasks with the same record scope cannot both reserve; a directory write conflicts with its child file even when the strings differ. Different worktree roots do not avoid a shared repository-record conflict. A late generation returns quarantined, with the artifact preserved.
- [ ] **Step 2: Run `python3 -m unittest tests.test_migrations tests.test_tasks -v`; expect missing-module/interface failures.**
- [ ] **Step 3: Implement versioned additive schema and transactional claims.** Persist project IDs, account snapshots, task scopes, attempts, leases, events, output/validation records and settings revisions. Use explicitly closed connections/WAL-safe transactions. Legacy imports are source-tagged and not automatically approved.
- [ ] **Step 4: Run concurrency/restart/import tests plus the existing store suite.** Assert task counts and ownership survive restart and no original queue file changes. Commit these files alone.

## Task 2: Provider registry, private config and capability-safe adapters

**Files:** Create `snooze/{providers,credentials}.py`, `snooze/adapters/{base,lightsprint,external,registered}.py`, corresponding tests; modify `accounts.py`/`transport.py` narrowly for compatibility.

**Interfaces:** `ProviderRegistry.list_public() -> list[dict]`, `upsert_public_config(account_id: str, values: dict) -> dict`, `test_connection(account_id: str) -> AccountSnapshot`; adapter methods `observe(session_id)`, `launch(task, attempt)`, `resume(session_id, attempt)`, `cancel(session_id)` and `collect(attempt)` return typed receipts/capabilities or a specific unsupported-operation result.

- [ ] **Step 1: Write failing registry/adaptor tests.** Renamed MCP keys retain verified workspace identity; ambiguous ownership is rejected; unavailable quota is null; private headers never enter DTOs; disabled accounts retain history. Unsupported launch/cancel is rejected before a network mutation.
- [ ] **Step 2: Run adapter tests and verify the intended failures.**
- [ ] **Step 3: Inspect configured LightSprint tool/API schema read-only before implementing mutations.** Record supported routes, receipt fields and model/effort options. Do not invent identity/quota APIs. Implement only confirmed operations with bounded timeouts and safe normalization; raw provider bodies remain private. Add private credential references and explicit approved endpoint/network scope checks.
- [ ] **Step 4: Implement registry configuration, manual quota overrides/expiry and scaffold adapters.** Local/SSH/Ollama/v0/Figma entries advertise unsupported operations until live implementations exist. Never auto-select OAuth accounts, install models or alter global Codex config.
- [ ] **Step 5: Run fake-adapter tests and one real read-only LightSprint observation.** Record its timestamp/status separately from task completion. Commit scoped registry/adapter/config changes.

## Task 3: Policy and durable approved-queue scheduler

**Files:** Create `snooze/{policy,scheduler,validation}.py`, `tests/{test_policy,test_scheduler,test_validation}.py`; wire `monitor.py`/daemon loop after isolated tests pass.

**Interfaces:** Shared types above; `ValidatorRegistry.validate(task: TaskSpec, artifact: dict) -> ValidationResult`; allowlisted validator IDs cannot supply arbitrary executable code. `Scheduler` is constructed with repositories, registry, policy, validators and injectable clock.

- [ ] **Step 1: Write failing policy tests.** Capacity is eligible configured capacity minus reservations, constrained by project/global/model limits and quota reserves. Disabled/depleted/unhealthy accounts are excluded. Unknown quota needs a valid configured override/budget policy. Native bulk routes remain excluded by default; quality/tool/privacy requirements are hard filters, not optional ranking preferences.
- [ ] **Step 2: Write failing scheduler tests.** Idle with missing artifact remains incomplete; valid output completes before replacement work; overlapping scopes rejected; ambiguous launch requires reconciliation; confirmed cancellation can release an owner; stale/expired lease alone cannot. Retry counters/backoff survive restart and cap at two recoveries. One broken account does not block healthy accounts.
- [ ] **Step 3: Run the new tests to see the missing scheduler/policy fail.**
- [ ] **Step 4: Implement eligibility and deterministic rank decisions.** Persist structured reasons and neutral priors for unmeasured quality/latency; choose approved model/effort only. Reserve transactionally, launch outside the transaction, reconcile receipts, collect and validate artifacts, fence stale attempts. Add bounded backoff/circuit breaker state and due-time scheduling. Availability signals wake the scan; durable polling recovers missed signals.
- [ ] **Step 5: Pin pause/emergency semantics.** Automatic dispatch/resume is blocked while paused; manual override is explicit and budget/lease-checked. Emergency stop blocks both until cleared. Authentication errors, quota exhaustion, validation failure and retry exhaustion have separate outcomes/incidents.
- [ ] **Step 6: Test shadow/external-managed mode.** Proposed decisions are recorded but provider mutation count stays zero. Explicit handover requires reconciled sessions and confirmed quiescence of the registered external owner. No handover occurs merely because monitoring looks stale.
- [ ] **Step 7: Run full scheduler/adapter/storage regression tests.** Prove no duplicate ownership across two competing tick calls or daemon restart. Commit scoped scheduler/policy/validation/loop integration.

## Task 4: Operational control API, live updates and frontend intervention

**Files:** Create `snooze/control.py`, `snooze/events.py`, API tests; modify web/CLI and the command-centre API client/Queue/Providers/Settings/TaskDrawer components.

**Interfaces:** `Control.apply(project_id: str, actor_id: str, action: str, target_id: str, values: dict, expected_revision: int) -> ActionReceipt`. Define `ActionReceipt(action_id, state, reason, revision)` in `control.py`. Actions include hold/approve/prioritize/resume/retry/cancel/reassign/account-config/policy-config/dispatch-pause/emergency-stop. Receipts distinguish requested, pending, confirmed and rejected.

- [ ] **Step 1: Write failing authenticated/revision tests.** Stale settings revision yields conflict; cross-origin requests fail; invalid limits/intervals fail; provider secrets never appear in responses. Unsupported/external-managed operations explain why they are disabled. Emergency stop cannot be bypassed by manual retry.
- [ ] **Step 2: Implement control handlers through repositories/policy, not direct ad hoc provider calls.** Persist actor/action/result. Validate settings revisions and wake the daemon so changes take effect without restart. Add bounded authenticated events with disconnect cleanup and polling fallback.
- [ ] **Step 3: Connect frontend controls and test them in Playwright.** Click pause/configure/retry/cancel against fake adapters and verify backend state/history after reload. Pending cancellation stays pending until a receipt; disabled operations do not send mutations. No optimistic fake success.
- [ ] **Step 4: Run API, frontend and scheduler regressions.** Commit scoped control/event/UI integrations.

## Task 5: Durable incidents and coordinator delivery

**Files:** Create `snooze/{outbox,notifications,mcp_server}.py`, `tests/{test_outbox,test_notifications,test_mcp_server}.py`; extend incidents UI/CLI/operator docs.

**Interfaces:** `Outbox.enqueue(incident_id: str, channel_id: str, payload: dict, due_at: float) -> str`; `deliver_due(now: float) -> list[DeliveryReceipt]`; `acknowledge(delivery_id: str, coordinator_id: str) -> bool`. Define `DeliveryReceipt(delivery_id, state, accepted_at, acknowledged_at, error_kind)` in `outbox.py`. MCP exposes scoped snapshot/incidents/task/control tools with the same backend auth/policy, not a bypass.

- [ ] **Step 1: Write failing persistence/dedup tests.** A recurring incident produces one active outbox request; restart retains due work; delivery failure retries with a cap; acknowledgment differs from resolution. Healthy unchanged state sends nothing.
- [ ] **Step 2: Write security/channel tests.** Destination allowlists reject arbitrary network targets; an allowlisted command uses argument arrays and no task-supplied shell. HTTP 200 marks delivery accepted, not coordinator-acknowledged. Missing documented wake support displays inbox-only.
- [ ] **Step 3: Implement local inbox/CLI/MCP and optional configured webhook/command channels.** Register coordinator/project scope; redact incident payloads; persist evidence, delivery receipt and acknowledgment. Do not inject into arbitrary GUI chats or create recurring native AI wakeups by default.
- [ ] **Step 4: Demonstrate end-to-end delivery to a test receiver and registered coordinator consumer.** Kill/restart before delivery, then prove it is recovered and acknowledged. Test a channel failure without losing the incident. Update UI/docs with tested channel support only.
- [ ] **Step 5: Run full regressions and commit.** One bounded live LightSprint recovery/dispatch must produce a provider receipt, saved artifact and validated outcome before release claims automatic recovery. Use an approved independent test queue; do not seize ongoing legacy work.

## Handoff

Fresh task reviews plus root integration precede a whole-branch security/ownership review. Continue to the historical analytics plan; do not call the complete user request finished after scheduler tests alone. Live project takeover is a separate explicit operator action after release gates.
