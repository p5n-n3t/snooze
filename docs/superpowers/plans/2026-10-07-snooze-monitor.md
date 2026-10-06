# Snooze Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Restore trustworthy Trump Files monitoring and expose it through a small reusable web dashboard.

**Architecture:** Python service with SQLite durable observations and incidents, provider adapters, a legacy queue reader and a static browser UI. Only one scheduler owns a project; integrate the existing supervisor before migrating its dispatch ownership. Separate live execution, observation freshness and validated artifacts.

**Tech Stack:** Python 3.11+, unittest, sqlite3, standard-library HTTP and file locking, plain HTML/CSS/JavaScript, Linux user services. No runtime dependency on Symphony or Docker.

**Spec:** docs/superpowers/specs/2026-10-07-snooze-monitor-design.md

## Global Constraints

- Localhost by default; credentials stay backend-only; mutation routes require origin validation and a control token.
- Default polling 300 seconds, minimum 30; default recovery retries 2.
- Default capacity 12 per account; higher limits require explicit verified configuration.
- Hide empty capacity rows; maintain completed history.
- Disable reported depleted account 1; verify account 2 before new dispatch.
- Never infer authenticated account identity from username suffix or old numeric index.
- No duplicate assignment, arbitrary shell commands, native-quota fallback, Neon writes or repository rename.
- Work is limited to the approved deterministic queue and approved model/budget settings.
- Preserve existing history; use sanitized fixtures; no private account details in GitHub.

## Review Focus

- Reordered/renamed MCPs must not send a historical task to a different account (Task 1).
- Timeouts and stale cached status must not become false running/completed reports (Tasks 2–3).
- An ambiguous launch or daemon restart must not create a duplicate worker (Task 3).
- Hostile task text/URLs and cross-origin requests must not expose secrets or execute browser content (Task 4).
- Existing supervisor ownership must prevent competing dispatch or destructive queue migration (Tasks 3 and 5).

## File map

Create snooze/accounts.py, transport.py, store.py, legacy.py, monitor.py, policy.py, web.py, cli.py and __main__.py; static/index.html, app.js and style.css; tests/test_accounts.py, test_store.py, test_monitor.py, test_web.py and test_cli.py. Add pyproject.toml, install.sh, README.md, docs/ADAPTERS.md, docs/OPERATIONS.md, SECURITY.md, LICENSE, THIRD_PARTY_NOTICES.md and .github/workflows/test.yml. Modify only the explicit legacy LightSprint discovery/API integration files when validated mapping is available; do not stage unrelated Trump Files edits.

### Task 1: Recover configured account access safely

**Files:** snooze/accounts.py, transport.py, tests/test_accounts.py; existing Trump Files scripts lightsprint_mcp.py and supervise_continuous_finish.py integration.

**Interfaces:** discover_accounts(config: dict) -> list[dict] returns server_key, label and configured capacity without secrets. resolve_owner(accounts: list[dict], workspace_id: str, observed_workspaces: dict) -> str returns exactly one verified server key or raises an ambiguity error. request(server_key: str, method: str, path: str, body: dict | None) -> dict performs bounded MCP requests.

- [ ] Write tests accepting both lightsprint7 and lightsprint-7-user, rejecting missing configuration keys, hiding token fields and refusing ambiguous/reordered owner mapping.
- [ ] Run `python3 -m unittest tests.test_accounts -v`; demonstrate failure before implementation.
- [ ] Implement explicit configured-key discovery and verified workspace/session ownership mapping; do not add implicit old-number aliases.
- [ ] Run tests; perform sanitized read-only discovery on enabled configured accounts. Retrieve identity/quota only through supported endpoints; unsupported means unknown.
- [ ] Commit scoped files. Legacy integration may be applied only after mappings are verified; reproduce the original naming rejection and prove a successful read afterward, separately from worker completion.

### Task 2: Durable observations and legacy import

**Files:** snooze/store.py, legacy.py, tests/test_store.py.

**Interfaces:** Store(path: Path), ingest_jobs(project_id: str, jobs: list[dict]) -> None, observe(session_id: str, observation: dict) -> None, snapshot(project_id: str) -> dict. read_queue(path: Path) -> list[dict] never rewrites the input queue. snapshot has accounts, workers, incidents, observed_at and freshness fields.

- [ ] Test idempotent import, original history retention, distinct requested/confirmed model fields, unavailable timestamps, corrupt/partially-written input and reopen persistence.
- [ ] Run `python3 -m unittest tests.test_store -v`; confirm failure.
- [ ] Implement SQLite transactions, immutable observation history and bounded retry of a partially-written queue read. Imported statuses retain their source timestamp and are stale until observed live.
- [ ] Run tests and inspect a sanitized Trump Files snapshot: exactly 84 migration assignments, no invented completed rows.
- [ ] Commit scoped files.

### Task 3: Persistent monitor and bounded recovery

**Files:** snooze/monitor.py, policy.py, tests/test_monitor.py.

**Interfaces:** Monitor(store: Store, adapter, policy: dict).check(project_id: str) -> dict records cycle start/end/errors. decide(job: dict, observation: dict, policy: dict) -> dict returns observe/resume/retry/escalate/none. Adapter supports observe, inspect_artifacts and explicitly advertised recovery operations. acquire_project_lease(project_id: str, owner: str) -> bool prevents competing actions.

- [ ] Test one timed-out account alongside a healthy account, quota exclusion, configured capacities, missing branches, idle with complete artifacts, restart leases, uncertain launch and exhaustion after two retries.
- [ ] Run `python3 -m unittest tests.test_monitor -v`; confirm failure.
- [ ] Implement bounded I/O, cycle timestamps, independently persisted observations, incident deduplication and leases. Account failures cannot erase unrelated successes.
- [ ] Integrate recovery through the existing validated supervisor, not a second dispatcher. Disable new recovery actions if existing ownership is unknown. Reassignment requires old-owner release or confirmed inactivity and preserved assignment history.
- [ ] Run tests; prove one approved recovery and validated artifact without duplicate ownership. If provider blocks it, expose exact evidence and do not claim this acceptance check passed.
- [ ] Commit scoped files.

### Task 4: Web dashboard and incident controls

**Files:** snooze/web.py, static/index.html, app.js, style.css, tests/test_web.py, SECURITY.md.

**Interfaces:** GET /api/state?project=ID returns Store.snapshot; GET /api/tasks/ID returns full local instructions; GET /api/incidents returns actionable incidents. POST /api/check, /api/settings and /api/incidents/ID/ack validate origin and token. Settings persist poll interval, pause_dispatch, enabled accounts, capacity and retry limit.

- [ ] Test escaped hostile instructions, unsafe URLs, missing mutation token, cross-origin writes, hidden vacant slots and minimum interval rejection.
- [ ] Run `python3 -m unittest tests.test_web -v`; confirm failure.
- [ ] Implement localhost server, secure mutations and compact dark dashboard with account cards, occupied rows, model/effort provenance, age/duration, task details, incidents and history filter. No credential fields in responses.
- [ ] Run tests plus browser verification of settings persistence, task links, truthful stale indicators and keyboard accessibility. Use text labels as well as colors.
- [ ] Commit scoped files.

### Task 5: CLI, service and coordinator handoff

**Files:** snooze/cli.py, __main__.py, pyproject.toml, install.sh, tests/test_cli.py, docs/ADAPTERS.md, docs/OPERATIONS.md, README.md.

**Interfaces:** snooze init --repo PATH; serve --open; status; incidents; check; config; service install. Init records coordinator ID and allowed repo path. Service install creates one user service; it does not silently stop another supervisor. A documented takeover requires backup, ownership release and explicit service handover.

- [ ] Test paths with spaces, missing Python prerequisite, second daemon lock rejection, incident acknowledgement and fresh install without Codex config.
- [ ] Run `python3 -m unittest tests.test_cli -v`; confirm failure.
- [ ] Implement per-user install without privileged package installation, CLI and user-service persistence. Register local/remote workers through documented JSON events; configured hosts do not become active workers by assumption.
- [ ] Document coordinator polling, future MCP capability contract and optional supported wake-up hooks. State clearly that universal GUI chat injection is unavailable. Check CLI help and startup on a fresh temporary repo.
- [ ] Commit scoped files.

### Task 6: Acceptance, publication and Trump Files handoff

**Files:** LICENSE, THIRD_PARTY_NOTICES.md, .github/workflows/test.yml, README.md, docs/OPERATIONS.md.

**Interfaces:** release evidence lists unit results, browser results, real provider read, recovery artifact validation and current unresolved incidents separately.

- [ ] Add tests/CI for the full suite and credential redaction. Record exact license/provenance for copied source; if no source is copied, state patterns were inspired rather than vendored. Use Apache-2.0 for original project code.
- [ ] Run `python3 -m unittest discover -v` and browser checks; verify a running user service, incident visibility and no competing scheduler. Confirm private data excluded from tracked files.
- [ ] Reconcile Trump Files saved results before new dispatch, then keep its remaining approved queue under the single monitor. No claim of finished corpus unless artifacts validate.
- [ ] Verify GitHub remote p5n-n3t/snooze, push scoped source and docs, set accurate description/topics and evidence-backed CI badges. Do not include private queue data or account identities in public docs; sanitize roadmap labels before publication.
- [ ] Commit completion evidence and save Mem0 checkpoint or milestone matching actual completion.

## Execution allocation

Preserve JQ's request for inexpensive delegation: root owns credentials, account mapping, legacy recovery and release checks. Delegate independent frontend and documentation tasks only after healthy provider access is proven, using explicit disjoint files and the smallest suitable available model. Avoid native subagents by default. Core dependent backend tasks run sequentially; more workers will not fix broken authentication or account ownership.

## Plan review

Spec coverage checked: occupied capacity, identity/credits uncertainty, monitor controls, persistence, local/remote registration, incidents, safe recovery, security, packaging and publication each have an owning task. Future fleet/design integrations remain roadmap-only. Written-plan approval is required before implementation.
