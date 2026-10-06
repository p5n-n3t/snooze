# Operations

Use separate `--state` directories for projects. `init` registers a repository and optional read-only JSON queue. Existing files are never modified by queue import. Do not rerun init on existing state until custom ownership mapping is backed up.

`serve` runs the web view and periodic observations in one process, guarded by an exclusive state lock. `check` cannot acquire the lock while serve owns it: use dashboard Check now. A local HttpOnly SameSite=Strict cookie and exact same-origin request are required for dashboard mutations. Programmatic requests may alternatively send the control token in X-Snooze-Token with the correct Origin.

The current monitor does not dispatch/resume/cancel anything. It can coexist with a legacy dispatcher in observation-only mode. Never enable future recovery in two controllers simultaneously. The original supervisor remains responsible for scheduling until a documented exclusive handover.

Incidents persist across restarts. Acknowledgement suppresses that incident key, not all future failures; incident lifecycle needs further refinement. Check settings through `status`. Stale is currently older than ten minutes; interval is adjustable, freshness threshold is not yet configurable.

Use a Linux user service for persistence; an installed example may be created for the current project. Generic service installation CLI is planned, not implemented. Logs contain cycle timestamps/counts, not tokens. Browser host is localhost only; remote hosting needs a separate authenticated design.
