# Adapter contract

Implemented: LightSprint read-only MCP transport and legacy JSON queue input. Account discovery is configuration-local; verified workspace ownership must be supplied. No public API is assumed for identity, quota or provider slots.

Observation returns status, model and effort, without raw provider output. Unknown effort stays unknown; the UI distinguishes requested values. Monitor uses four I/O threads, not four AI agents. Adapter exceptions become unavailable observations and incidents rather than fabricated failures.

Planned capability flags: identity, quota, observe, artifacts, launch, resume, cancel and notifications. Scheduling is not implemented yet. Future providers must advertise only operations actually supported. CLI/HTTP interfaces are usable by agents with local access; an MCP facade and arbitrary GUI chat wake-up are not implemented.
