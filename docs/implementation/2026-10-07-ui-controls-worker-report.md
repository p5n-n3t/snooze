# Snooze UI controls repair report

## Scope and result

Completed the UI repair and bounded Task 4 controls in `p5n-n3t/snooze` on the existing task branch, `ls/13-snooze-command-centre-svelte-ui-implemen-m68a`. The first UI commit `edb56f9` and all append-only history remain intact. The task branch includes the latest coordinator updates available during this run, through `origin/codex/snooze-command-centre` at `eaf4db9`; they were merged without rebasing or force-pushing. Authored follow-up changes are confined to `frontend/`, generated `snooze/static/`, and this report.

The three Important findings are fixed:

- History now requests `/api/v2/history/events` in server pages of 25, carrying offset and search to the server instead of downloading the full state snapshot.
- Provider credentials render as unreported/unknown unless the API supplies evidence; account labels and key names no longer imply verification.
- Dashboard refresh uses one abortable, timed flight at a time, with recursive settled polling, capped backoff, last-good state retention, and stale-data messaging. Generation-aware query timing remains in place, and the poller is cleaned up when the app unmounts.

The five command-centre pages now expose the bounded coordinator controls. Providers has a safe account add/edit form, revision-aware save and connection test, and capability/rejection reasons; it has no credential input. Settings saves operational policy and conservative/balanced/custom presets, reports persisted pause/emergency state, and accurately disables external-owned controls. Queue reads bounded server pages and supports draft, approval, hold, priority, retry, and pending cancellation actions; unsupported reassignment stays disabled with its reason. Watch separates occupied slots from confirmed/requested values and shows durable delivery receipts, coordinator registration, and receipt acknowledgment without implying resolution or arbitrary GUI wakeup. The typed client displays confirmed, pending, and rejected receipts with their reasons, revisions, and HTTP status; no optimistic success is shown.

## Verification

The final verification ran on 2026-10-07 using Node `v22.19.0`, npm `10.9.3`, and Python `3.11.6`.

| Command | Result |
| --- | --- |
| `npm run check` | Passed: 0 Svelte errors and 0 warnings. |
| `npm test` | Passed: 9 test files and 15 tests. Coverage includes bounded history, typed receipts, account/policy persistence, capabilities, and serialized polling. |
| `npm run build` | Passed: Vite emitted the hashed JS/CSS, self-hosted fonts and logo; `package-assets.mjs` replaced obsolete bundles and copied notices into `snooze/static/`. |
| `npm run e2e` | Passed after the latest coordinator merge: all 4 Playwright tests against Snooze's Python HTTP handler. This covers receipt states and control persistence, capability gates, acknowledgment semantics, cancellation remaining pending while ownership persists, both themes, desktop/mobile layouts, keyboard focus, and a hanging state endpoint with no overlapping requests and teardown. |
| `python3 -m unittest discover -s tests -p 'test_tasks.py' -v` | Passed after the coordinator merge: 11 task repository tests, including the new guarded handover case. |
| `python3 -m unittest discover -s tests -p 'test_scheduler.py' -q` | Passed after the latest coordinator merge: 13 scheduler tests, including monitor resource and preset behavior. |
| `python3 -m unittest discover -s tests -p 'test_transport.py' -q` | Passed after the latest coordinator merge: 3 transport tests. |
| `python -m pip wheel . --no-deps --no-build-isolation --wheel-dir /tmp/snooze-wheel-final` plus wheel-member assertion | Passed: built `snooze_workers-0.1.0-py3-none-any.whl` (1,155,761 bytes); all 9 required current bundle/index/license entries were present. |
| `git diff --cached --check` on authored sources | Passed. The generated one-line Vite bundle contains an intentional whitespace-character literal, which Git's whitespace check reports as trailing whitespace; no authored source has trailing whitespace. |

The final browser fixture reported 100 active worker rows and a 51,445-byte schema-v2 state response. With 10,002 history events, the history request returned 5,820 bytes and the page rendered 25 rows. These are fixture measurements, not production-load guarantees. The Vite output was 151.41 kB JavaScript and 59.16 kB CSS before gzip.

## Rendered evidence

The nine current browser screenshots are attached under their existing labels: Watch dark/light on desktop and mobile, Queue, Providers, History, Settings, and the mobile task drawer. Playwright rendered them through the real Python HTTP handler with the production static bundle; the screenshot artifacts were uploaded and registered with source coverage. The stack has no configured preview service (`inspect_preview` confirmed there is no live app route to capture), so the server-side preview capture tool was unavailable. After the coordinator merges changed task ownership and monitor/policy scheduling behavior, Watch dark desktop and Settings were recaptured and now cover the relevant runtime, scheduler, policy, and task ownership sources; remaining views are covered by unchanged UI sources. The later history-review update was documentation-only. The browser test also asserts no external requests and no console/page errors.

## Reuse, licensing, and limits

The Tokyo Nights design, local logo and fonts remain in use. Existing provenance and license notices are retained and packaged: selected kit-ui adaptations pinned to `ceff715d835017daa9ec099446fa6ce71233829f` (Apache-2.0), the generation-aware AgentsView timing pattern pinned to `f4eacbc61119ebc2bfcaa47f141eb8103cf3edf1` (MIT), Lucide Svelte (ISC), Svelte (MIT), and Figtree/JetBrains Mono (SIL OFL 1.1).

No backend files were edited by this follow-up; coordinator changes were merged unchanged from the explicitly requested branch. The controls honor the API's ownership and capability boundaries: no secret material or private backend configuration is exposed, native execution remains off by default, and cancellation is described as pending until provider acknowledgment. Rich analytics presentation, production deployment, Neon, and other repositories remain outside this bounded UI work.
