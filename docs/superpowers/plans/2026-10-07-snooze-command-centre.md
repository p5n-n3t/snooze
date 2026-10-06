# Snooze Command Centre Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the preview with a polished, lightweight dashboard and reliable launch experience without disturbing the running scheduler or history.

**Architecture:** A production Svelte build is served by the existing Python localhost service. A versioned, safe read model adapts legacy observations into the new interface; mutation controls use capability checks rather than pretending future scheduler functions exist. This is the first of three independently verifiable plans; the control-plane and analytics plans complete the approved specification.

**Tech Stack:** Python 3.11+, SQLite, Svelte 5/TypeScript, pinned kit-ui, LayerChart/D3 where extracted panels need them, unittest, Vitest and Playwright. Node is build/test time only; this machine has Node 26.3.1.

**Spec:** `docs/superpowers/specs/2026-10-07-snooze-command-centre-design.md` (written specification approved by JQ, 2026-10-07).

## Global Constraints

- Product name is Snooze; Trump Files is a monitored project.
- Default observation interval 300 s, minimum 30 s. Monitoring I/O concurrency remains separate from worker-slot capacity.
- Preserve existing state/history and external dispatcher ownership. No Neon writes, repository rename, global configuration changes or second live dispatcher.
- Dark surfaces `#1a1b26`/`#24283b`; accents `#7dcfff`, `#7aa2f7`, `#bb9af7`, `#f7768e`; light colors must be accessible darker equivalents.
- Reuse kit-ui at `ceff715d835017daa9ec099446fa6ce71233829f`; extracted AgentsView code comes from `f4eacbc61119ebc2bfcaa47f141eb8103cf3edf1`. Preserve licenses, copyright and modification notices.
- Figtree and JetBrains Mono are self-hosted with font notices. No external font requests or background AI monitoring calls.
- New private APIs require authentication; mutations retain host/origin checks. Credentials remain backend-only.
- Preserve the user's delegation preference: cheap/remote bounded workers, root integration/review; do not silently inherit an expensive model or create a native worker swarm.

## Review Focus

- Folder names containing spaces or identical basenames must not collide or corrupt dashboard routes: pinned in Task 1/3.
- Provider idle, unavailable or stale must not become task-complete or count as confirmed running: pinned in Task 1/2.
- Opening an existing daemon must not reinitialize ownership or launch a second process: pinned in Task 3.
- Malicious task text, URLs, encoded paths and symlinks must not escape static serving or leak configuration: pinned in Task 1/2.
- Thousands of terminal records must not inflate live occupancy or freeze rendering: pinned in Task 2.

## File boundaries and shared contract

`snooze/views.py` owns projections; `snooze/web.py` owns routing/authentication; `snooze/cli.py` owns launch lifecycle. Frontend code lives in `frontend/`; compiled assets are packaged under `snooze/static/`. Do not edit the legacy Trump Files dispatcher from this plan.

`dashboard_state(store: Store, project_id: str, config: dict, now: float) -> dict` returns schema version 2: `project`, `summary`, `accounts`, `slots`, `incidents`, `settings`, `capabilities`, `cycle`. Slots include `task_id`, `session_id`, `account_id`, `logical_slot`, `task_summary`, `requested_model`, `confirmed_model`, `requested_effort`, `confirmed_effort`, `started_at`, `observed_at`, `provider_state`, `task_state` and `observation_freshness`. Unknown fields are null. Capabilities have `supported` and `reason`; external-managed projects cannot dispatch.

`task_detail(store: Store, project_id: str, task_id: str) -> dict | None` returns allowlisted instructions, attempts/events and validated HTTPS references. It does not expose provider headers/raw config. Preserve the current v1 APIs for compatibility until a documented removal.

## Task 1: Versioned private dashboard API

**Files:** Create `snooze/views.py`, `tests/test_views.py`; modify `snooze/web.py`, `tests/test_web.py`.

**Interfaces:** Consumes current `Store.snapshot(project_id)` and account discovery without credentials. Produces the two functions above and authenticated GET `/api/v2/state`, `/api/v2/tasks/{id}`. Existing authenticated settings/check/ack controls remain available. New read APIs use the same private cookie or CLI token; untrusted origins cannot obtain task data.

- [ ] **Step 1: Write failing projection tests.** `test_idle_is_not_completion` asserts `state["slots"][0]["provider_state"] == "idle"`, `state["slots"][0]["task_state"] != "complete"` and `state["slots"][0]["confirmed_effort"] is None`. `test_external_owner_disables_dispatch` asserts `state["capabilities"]["dispatch"]["supported"] is False`. Stale/unavailable fields retain provenance; confirmed model null does not copy requested model. Two paths `/a/shared` and `/b/shared` remain distinct. Projection excludes `Authorization`, `http_headers`, raw config and arbitrary provider fields.
- [ ] **Step 2: Run `python3 -m unittest tests.test_views tests.test_web -v`.** Expect failure for the missing projection and private routes, not unrelated preview tests.
- [ ] **Step 3: Implement projections and routes.** Keep project identity compatibility explicit; do not silently merge or rewrite current jobs. Parse task IDs safely. Distinguish task/observation states and active reservations from historical sessions. Include cycle timestamps from actual checks, not an invented fixed cadence.
- [ ] **Step 4: Add static-path/auth tests.** Assert unauthenticated private read fails; same-origin cookie read works; cross-origin mutation fails; encoded `..`, a symlink escaping the static root, and nonexistent files never serve arbitrary content. Implement production hashed-asset serving with a confined root and correct MIME types.
- [ ] **Step 5: Run all 16 existing tests plus new API tests.** Expected all pass. Commit only API/projection/tests.

## Task 2: Polished Svelte command centre

**Files:** Create `frontend/package.json`, lockfile, `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.ts`, `src/App.svelte`; create `src/lib/{api,theme,format}.ts`, `src/components/{Shell,Watch,Queue,Providers,History,Settings,TaskDrawer}.svelte`, component tests and `e2e/dashboard.spec.ts`; modify Python package-data/build configuration and provenance notices.

**Interfaces:** Consumes API schema version 2; produces production assets served by Task 1. Page components do not depend on legacy queue shapes. A shared API client reports pending/confirmed/error results; it never renders a mutation as successful from a button click alone.

- [ ] **Step 1: Write UI tests against fixed schema-v2 fixtures.** `unsupported_resume_is_disabled` uses a single-slot fixture and asserts `expect(screen.getByRole("button", {name: "Resume"})).toBeDisabled()`. `unknown_effort_is_not_requested_effort` asserts the confirmed-effort cell says `Unknown`, not the requested `low`. Assert occupied rows only, completed sessions in history, hostile prompt text rendered literally and unsafe URLs not clickable. A 10,000-history/100-worker fixture renders a bounded page rather than 10,000 DOM rows.
- [ ] **Step 2: Pin minimal dependencies and run the tests.** Define npm scripts `test` for `vitest run`, `build` for the production Vite build, `check` for `svelte-check`, and `e2e` for `playwright test`. Run `npm --prefix frontend test`; expect missing component/behaviour tests fail before implementation. Use the inspected kit-ui commit and supported Svelte/build packages; record actual resolved versions, not invented ones. Preserve upstream/component/font notices from the first copy.
- [ ] **Step 3: Implement shared shell/design tokens.** Adapt kit-ui tables, menus, forms, settings layout and drawer/dialog primitives. Apply the approved palette, local fonts, generated logo, strong hierarchy, compact rows, project picker, persistent pause/emergency indicators, dark/light toggle and reduced-motion behaviour. No bare mismatched controls, blanket glow or fake charts.
- [ ] **Step 4: Implement pages/drawer using the API client.** Watch prioritizes occupied slots and actionable incidents; Queue shows task status and capability-aware interventions; Providers exposes safe account labels/configuration capability; History shows actual available events and truthful unsupported analytics; Settings persists supported interval changes. Pause/emergency controls remain disabled with an external-owner reason unless the responsible executor advertises that capability: a preview's local pause flag cannot be represented as pausing the legacy dispatcher. Full provider/queue controls become live through plan 2 without redesigning these components.
- [ ] **Step 5: Adapt AgentsView `LiveQuery` and event refresh patterns.** Preserve source notices and generation-aware timing. Background failures display stale data with a warning rather than resetting counts to zero. Keep bounded polling until the event stream from plan 2 is available.
- [ ] **Step 6: Verify production assets in Playwright.** Run `npm --prefix frontend run check`, `npm --prefix frontend run build` and `npm --prefix frontend run e2e`; expect successful checks/build and all browser tests pass. Serve through the Python backend, not `file://`. Assert no console errors/external font requests; task drawer and keyboard focus work; screenshots at 1440×900 and 390×844 in both themes; contrast/reduced-motion tests pass. Verify changes persist after browser reload.
- [ ] **Step 7: Verify packaged asset inclusion.** Build a wheel in the project environment and inspect its asset list; install to a temporary environment and load the dashboard. No Node process is required at runtime. Record resource measurements for the representative fixture. Commit scoped frontend/assets/package/provenance changes.

## Task 3: One-command launch and release documentation

**Files:** Modify `snooze/cli.py`, `install.sh`, `README.md`, `docs/OPERATIONS.md`, `.github/workflows/test.yml`; create/update CLI tests and a service-install helper scoped to the user account.

**Interfaces:** `open_dashboard(state: Path, port: int, open_browser: Callable[[str], bool]) -> str` probes the configured compatible daemon and returns its URL. `snooze` and `snooze open` use it; explicit `serve` remains foreground mode. Existing `--state` selection remains supported.

- [ ] **Step 1: Write lifecycle tests.** Starting twice uses one owner; an unrelated process on the port is rejected; a path with spaces works; opening does not call `prime` or overwrite ownership. A stopped configured user service is started and checked with a bounded readiness wait. Browser launch failure still prints a usable URL.
- [ ] **Step 2: Run `python3 -m unittest tests.test_cli -v`.** Expect new launch tests fail while existing prime test passes.
- [ ] **Step 3: Implement launch/service packaging.** Default opening respects the installed project/state binding; use subprocess argument arrays and registered user-service references, not arbitrary task commands. Fresh install supplies built assets and a first-run setup flow. Do not silently change global Python/Node or external services.
- [ ] **Step 4: Verify a fresh install and an existing-service open.** Existing ownership/history checksums remain intact. Current `snooze.service` survives the release switch; no duplicate listener. All Python/frontend/browser tests pass before restart.
- [ ] **Step 5: Document exact launch/recovery commands and current limitations.** Update GitHub metadata/badges only to tested functionality, publish release evidence and scoped commits. This phase alone is not completion of the full scheduler/analytics specification.

## Execution order and review

Task 1 defines the contract before Task 2 integrates it. Frontend visual work and Task 3's test-first lifecycle work can run in disjoint write scopes after Task 1's interface is locked. A fresh reviewer checks each task; root performs integration and a whole-branch review. Next execute the control-plane plan, then the analytics plan. Never stop after a pretty screen and claim the full request finished.
