# Snooze UI worker: approved Task 2

Read the Task 2 section in `docs/superpowers/plans/2026-10-07-snooze-command-centre.md` first; it is your requirements, with exact tests/values. Read spec sections 4, 9 and 10 for design/security. API shape is implemented in `snooze/views.py`. No need to read unrelated project transcripts or other repositories.

Work ONLY in p5n-n3t/snooze, from `codex/snooze-command-centre` at 260bd98 or a newer coordinator commit. Use your own cloud branch, do not overwrite the integration branch. Other workers own Python control/analytics modules.

## Ownership and output

Own `frontend/`, `snooze/static/` generated build, `pyproject.toml` package-data only, `THIRD_PARTY_NOTICES.md` and UI reuse/font licenses. Do not edit web.py, cli.py, scheduler, store, migrations or Trump Files. No subagents. No automatic merge, deployment, external services or global configuration. Node is build time only.

Implement the full five-page responsive shell and drawer, not a mock image. Preserve working legacy interval/check/ack controls; unsupported mutation controls are visibly disabled with reasons. New control API integration is coming separately. A shared action client should accept a future `{action,target_id,values,expected_revision}` POST to `/api/v2/control` and report the backend receipt, never optimistic success.

## Design plan, reviewed against the user's brief

This is a night-shift control room, not a marketing landing page. A quiet 208px navigation rail carries the generated crescent/alarm/connected-worker logo; the main surface is an occupied-worker roster and intervention inbox. Do not chop everything into identical cards. Account headers, row rules and hierarchy encode actual ownership. One brand accent area; no glow behind text, gratuitous gradients, ALL-CAPS labels or fake uptime/usage charts.

Palette: midnight #1a1b26, raised ink #24283b, cyan #7dcfff, periwinkle #7aa2f7, lavender #bb9af7, alert pink #f7768e. Light uses warm lilac-white surfaces and darker readable inks. Figtree for UI, JetBrains Mono only for identifiers/numbers. Use the existing transparent logo `docs/assets/snooze-logo-concept-v1.png`, self-host it and fonts.

Watch: project selector, last actual check, stale/connection warning, Check now, theme, persistent pause/stop reasons. Occupied rows grouped by account: slot, model/effort confirmed vs requested, truncated assignment, elapsed/observed, status and Inspect. Hide wholly unused and terminal rows, but retain account occupancy/capacity explanations. Show nulls as Unknown, never fill effort/model from requested values.

Queue: bounded searchable/paginated roster, tasks and supported intervention buttons. Drawer uses a focus-trapped upstream detail drawer, shows full instructions literally, evidence links and requested/confirmed state. Providers: account summaries plus configuration-ready forms; no secret input echoed. History: real available evidence and missingness; reserve a clean interface for the rich report coming next. Settings: upstream settings layout, useful groups and interval persistence; don't pretend an observation-only pause flag controls the external dispatcher.

## Substantial, license-preserving upstream reuse

Vendor selected controls/styles from kenn-io/kit-ui commit ceff715d835017daa9ec099446fa6ce71233829f rather than inventing a second design system. Use its tables, forms/buttons/select/search, settings layout and drawer/focus/overlay helpers. Keep Apache-2.0 copyright/license and prominent modification notices. Copy Figtree/JetBrains Mono WOFF2 and complete OFL font notice. Keep dependency footprint bounded: no entire demo/markdown/mermaid platform.

Adapt AgentsView `frontend/src/lib/utils/liveQuery.svelte.ts` at f4eacbc61119ebc2bfcaa47f141eb8103cf3edf1, generation-aware timings and bounded refresh pattern with MIT notices. Failed refresh retains the last real state with a warning, not invented zeroes. Do not copy its global stores/i18n/parser/database graph wholesale. Record exact origin, files, pin, modifications and license in the notices inventory.

## Verification/report contract

TDD: write and run the plan's behavioral tests RED before implementation. Then production Svelte checks/build, component tests, and Playwright against Python HTTP (not file://). Test both themes at 1440x900 and 390x844, keyboard drawer/focus, reduced motion, malicious text/link, unknown effort, unsupported Resume, pagination and no console errors/external fonts. Browser GET authentication uses the cookie and normal same-origin fetch metadata; do not try forging forbidden Origin headers. Screenshot verification must be rendered output, not bounds or source inspection.

Ensure nested built assets are in a wheel; no Node runtime. Create a report `docs/implementation/2026-10-07-ui-worker-report.md` with RED/GREEN commands/output, versions, files, screenshots, provenance and limitations. Commit/push only Snooze changes to your own branch and open a draft PR targeting codex/snooze-command-centre. Return branch, commits, PR, tests and actual outstanding concerns. Keep working until your bounded task is finished, not after the first build.
