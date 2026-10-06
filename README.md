# Snooze

[![Tests](https://github.com/p5n-n3t/snooze/actions/workflows/test.yml/badge.svg)](https://github.com/p5n-n3t/snooze/actions/workflows/test.yml)

Local-first visibility for distributed AI workers. A small web dashboard, durable observations and actionable incidents—without spending model tokens on monitoring.

**Status: early observation-only preview.** Automatic recovery, capacity-aware dispatch and universal agent wake-up are not implemented. Do not use this version as proof that a worker completed its assignment.

## Install and run

Python 3.11+ required. From this checkout:

```bash
bash install.sh
~/.local/bin/snooze init --repo /absolute/path/to/repo --queue /absolute/path/to/queue.json
~/.local/bin/snooze serve --open
```

The installer uses a dedicated virtual environment; no sudo or system package changes. On a fresh system, install Python/venv using your operating system first. The server binds to 127.0.0.1:8765.

Supported commands: init, serve, status, incidents, check, config. Use `--state PATH` before the command to select another project. Dashboard controls require the local token in STATE/control-token; paste it into the password field. Do not publish this token.

## What it shows

- Occupied worker rows grouped by mapped provider key or explicitly unverified legacy account.
- Requested versus provider-confirmed model/effort, last observation and time since launch.
- Full task instructions, historical results, stale/unavailable status and failure inbox.
- Persisted polling interval and manual check/acknowledgement controls.

LightSprint credentials remain in the configured local Codex TOML. Historical jobs need a verified workspace-to-server-key mapping in local project.json `ownership`. Renumbered accounts are never auto-matched by number. Without a mapping, status is ownership_unknown, not running. Credits/identity are currently unavailable; configuration labels are not authenticated identity.

The daemon observes every configured interval (default 300 seconds); API latency extends cycles. It does not claim an exact five-minute response guarantee. SSH/Ollama/v0/Figma scheduling remains roadmap work. Local worker registration and capacity settings are also not implemented in this preview.

## Developer checks

```bash
python3 -m unittest discover -v
```

Read [the design](docs/superpowers/specs/2026-10-07-snooze-monitor-design.md), [roadmap](docs/ROADMAP.md), [adapter contract](docs/ADAPTERS.md) and [operations guide](docs/OPERATIONS.md). Original code is Apache-2.0; see THIRD_PARTY_NOTICES.md. Never commit state, credentials, task data or private account identities.
