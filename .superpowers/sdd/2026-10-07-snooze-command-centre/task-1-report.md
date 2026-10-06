# Task 1 implementation report

## Result

Implemented the versioned private dashboard read API and projection. The public health response is limited to `{name: "snooze", api_version: 2, project: project}`. Existing v1 reads and authenticated settings/check/ack controls remain intact.

## RED

Command: `python3 -m unittest tests.test_views tests.test_web -v`

Result before implementation: failed to import `snooze.views` and `_make_server`, confirming the requested projection and route test surfaces were missing. Exit code 1.

## GREEN

Command: `python3 -m unittest tests.test_views tests.test_web -v`

Result after implementation: 10 tests passed. Coverage includes idle versus completion, stale/unavailable provenance, requested versus confirmed values, duplicate workspace basenames, external dispatch capability, allowlisted task detail, authenticated state/detail routes, same-origin cookie access, cross-origin mutation rejection, public health shape, and confined hashed static assets with MIME types.

Command: `python3 -m unittest tests.test_accounts tests.test_cli tests.test_monitor tests.test_store tests.test_transport tests.test_views tests.test_web -v`

Result: all 23 in-scope tests passed (16 existing plus 7 new). `git diff --check` passed.

## Broader discovery note

`python3 -m unittest discover -s tests -v` ran 33 tests and reported 31 passing plus two failures in `tests/test_migrations.py`: one expects a backup path but receives `None`; another expects an injected migration rollback hook to raise, but it is not called. Those tests/files are outside Task 1 ownership and were not modified. The `tests.test_tasks` checks passed.

## Changed files

- `snooze/views.py` — schema-v2 state and task detail allowlists, safe references, nonterminal task projection, capability reporting.
- `snooze/web.py` — authenticated `/api/v2/state` and `/api/v2/tasks/{id}`, public metadata-only `/api/health`, confined static serving with MIME detection, backward-compatible `serve(..., project_config=None)`.
- `tests/test_views.py` — projection and detail tests.
- `tests/test_web.py` — API authorization, health, origin, and static-path tests.

## Notes

No cycle timestamps are available in the unchanged Store snapshot, so the projection reports null cycle timestamps instead of synthesizing a cadence. Dispatch remains unsupported; no cloud worker or external ownership capability was advertised by account discovery. No service restart, global configuration, Neon operation, or push was performed.
