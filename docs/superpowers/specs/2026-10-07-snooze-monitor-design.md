# Snooze first version: finish work, not build a platform

Date: 2026-10-07. Status: design for user review; implementation has not started.

## Purpose and boundaries

JQ needs an inexpensive, persistent, readable supervisor that helps finish Trump Files without manually asking about every worker. Build a small local-first web dashboard around the existing queue and validated-output workflow. Do not require Symphony, Linear, Docker, or a large observability stack. The original coordinator remains responsible for editorial decisions and ambiguous repairs. No automatic live database writes or repository rename.

Only the first-version scope below is proposed for implementation. Future fleet orchestration is recorded separately in ROADMAP.md. Medium reasoning is sufficient for routine implementation; use stronger review only where justified by a specific ambiguity or security decision.

## Recommended approach and alternatives

Recommended: a small Python service, SQLite state, and a static browser interface; standard-library backend where practical. One daemon owns polling and durable scheduling. A legacy queue adapter reads Trump Files without pretending its cached state is live. Keep provider-specific code behind adapters. Avoid a second independent dispatcher competing with the current supervisor.

Alternative 1: a read-only dashboard over the existing supervisor. Fastest visibility but retains its stalled scheduling and account-name assumptions.

Alternative 2: deploy full Symphony/AgentOps/Langfuse. More infrastructure and integration work than this first run warrants. Borrow suitable design patterns or small licensed modules after checking their exact license and recording provenance, rather than adopting a whole platform.

## First-version components

1. Persistent monitor: bounded concurrent API requests, independent per-account failures, timeouts, actual cycle timestamps, checkpointed retries, and recovery after restart.
2. Adapter boundary: discover configured LightSprint servers regardless of username suffix; explicit account enablement, capacity and quota state. Legacy Trump Files queue and local-worker registration are supported inputs. SSH remains through the current coordinator; remote adapter registration is scaffolded, not an autonomous fleet deployment.
3. Durable state: projects, accounts, logical capacity positions, worker sessions, assignments, observations, incidents and actions. Store requested versus confirmed model/effort separately. Preserve original queue history and account/session ownership.
4. Browser view: project selector, account cards, occupied slot rows, alert inbox, short activity timeline, settings and task detail page. Empty capacity rows are hidden. Completed sessions move into history; a filter can reveal them.
5. Coordinator interface: structured incident inbox and a documented local API/CLI for reading and acknowledging incidents. A later MCP adapter exposes this to compatible agents. Automatic chat wake-up is capability-dependent, never promised universally.

## Account and capacity rules

Configured MCP names currently have the form lightsprint-N-username. Username suffix is a user-supplied label, not proof of the authenticated account identity. Retrieve provider identity if available; otherwise show the label and stable configuration ID, with source indicated. Never expose API tokens.

Default configured capacity is 12 per enabled account. Capacity is not a provider slot identifier. A user may configure a different proven limit (including 16 for a suitable model/account); unverified higher capacity is not used automatically. Models and effort are selected by task needs and policy, not always low reasoning.

Available concurrency is the sum of each eligible account's remaining configured capacity, minus its active reservations, constrained by project budget and queue size. Do not blindly multiply all configured MCPs by 12. Disable account 1 for dispatch based on JQ's depletion report; treat account 2 as uncertain until checked. Unknown quota is explicitly unknown. Provider credit figures include source and retrieval timestamp. Comments/removal from config stop new dispatch, but retained sessions remain visible in history.

## Worker rows and status

Each occupied logical slot shows account, model, effort, started time, elapsed duration, last observation, status and truncated task. Clicking opens full assigned instructions, attempts and errors in Snooze; use a provider task link only when its URL is verified.

Separate provider execution from artifact readiness: queued, starting, running, idle, failed, provider-completed, output-saved and output-validated. Stale/unavailable are observation conditions, not proof of failure. A successful launch is not completion. Missing Git branches are not proof that an agent failed.

## Scheduling and controls

Controls: check now; poll interval (default 300 seconds, minimum 30); pause new dispatch while observation continues; conservative/balanced profiles; enabled accounts; per-account capacity; retries (default 2); timeouts; stalled-session threshold; project concurrency ceiling. Show actual last successful cycle and next expected check: a configured five-minute interval alone is not a five-minute guarantee.

On idle or failed sessions, first inspect task state and saved artifacts. Validate completed output before assigning more. Resume a confirmed incomplete session where supported. Retry transient transport errors with bounded backoff. Quota exhaustion disables new dispatch for that account and generates an incident. Ambiguous launch outcomes require reconciliation before any retry. Reassignment requires ending/releasing the old owner or confirmed inactivity. Never run competing workers on the same records.

Initial automatic actions are confined to an explicitly primed project queue and approved models/budgets. No arbitrary shell execution, credential selection, database edits or new account creation. New work comes from a deterministic queue supplied by the coordinator, not invented busywork. Idle capacity is normal when no eligible work remains.

## Agent cooperation

The initiating agent primes Snooze with repo path, queue adapter, policy, task ownership and a coordinator identifier. Incidents carry account/session/task IDs, evidence, last action and suggested next step. Acknowledgements and leases prevent repeated repair by multiple coordinators. Desktop notifications and a persistent inbox work without AI. Only a documented, explicitly configured wake-up hook can trigger an agent automatically; otherwise the agent reads the inbox on its next turn. Do not claim a desktop chat can be messaged through an unsupported interface.

## Security and deployment

Bind to localhost by default. Restrict allowed repo paths; escape task text; validate links; enforce origin checks and a local control token for mutations. Keep tokens backend-only and redact logs. A future remote deployment requires authentication and network restrictions, not simply binding to all interfaces. Do not read arbitrary credential stores or copy keys to VMs. Keep a single scheduler owner using a lock and durable leases.

Proposed commands: snooze init --repo PATH; snooze serve --open; snooze status; snooze incidents; snooze check; snooze config; snooze service install. These are planned interfaces, not installed commands yet. Linux user-service support provides persistence without keeping this chat open. The installer checks prerequisites and reports changes without silently installing privileged system packages.

## Verification and definition of done

Tests cover discovery of renamed MCPs, disabled/depleted accounts, capacity math, restart recovery, stale observations, bounded failures, ambiguous launches, duplicate-assignment prevention, output validation and secret redaction. Browser checks cover task links, hidden empty slots, settings and truthful statuses. Prove one real LightSprint status read and one approved recovery flow, then collect and validate its output. Demonstrate incident delivery separately from automatic chat wake-up.

Deliver source, installer, README, adapter contract, operator guide, security notes, roadmap, tests and license/provenance notices in p5n-n3t/snooze. Publish no private queue content, account email addresses or credentials by default. GitHub description/topics/badges describe tested functionality only.

## Immediate Trump Files recovery order

1. Fix configured-name discovery and map existing jobs by verified account/workspace identity, not their old numeric aliases alone.
2. Read session/task evidence and recover already-saved artifacts before relaunching anything.
3. Determine actual healthy accounts; exclude depleted ones; release or reconcile stale ownership.
4. Feed the remaining disjoint assignments into one supervisor; track artifacts through validation.
5. Complete offline reconciliation with preserved history. Assess repository rename separately after work and integrations are safe.

Inspection on 2026-10-07 found nine renamed MCP entries. The legacy queue last updated on 2026-10-06 and still reports 84 nonterminal migration jobs and zero collected rows; this is stale local evidence, not a new live provider status.
