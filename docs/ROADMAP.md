# Snooze roadmap and JQ's infrastructure notes

Captured 2026-10-07. This document is a reusable briefing for future AI sessions. Plans are not claims of deployed functionality or verified capacity.

## Product intent

Open-source, easy-to-use, visual monitoring and eventually orchestration for heterogeneous AI workers. Prioritize saving local ChatGPT quota, tokens and laptop resources. Users describe an outcome to their preferred agent; that coordinator translates it into bounded work and delegates appropriately. Keep configuration dynamic: add/remove providers, accounts, models, tools and machines without rewriting the product.

## Phase 1 — small working monitor

Finish Trump Files first. Persistent configurable monitoring, truthful status, LightSprint account discovery, occupied capacity rows, recovery incidents and deterministic approved-queue scheduling. Leave SSH orchestration with Codex for now. Do not consume shared native quota on VMs merely to increase worker counts.

## Phase 2 — fleet workers

JQ reports ora5 and ora6 as available 4 OCPU / 24 GB RAM machines. Ora7 is being prepared, not yet ready. Target three, potentially four or more, Oracle ARM machines of that size. aws2 has 2 GB RAM and is intended for lightweight services/gateway duties, not assumed capable of heavy model inference. Verify hardware, OS, connectivity and workloads before scheduling.

Use Tailscale connectivity where configured; SSH can remain a maintenance/control transport over that network. Host a small worker service with authenticated jobs, heartbeats, cancellation, resource limits and artifact return. Support Ollama models selected according to measured task accuracy, RAM, context length and latency. CPU/RAM alone do not establish useful model speed or multimodal capability. Benchmark before replacing cloud workers. Do not install or expose model endpoints automatically.

Potential fleet MCP gateway location: locally or a small EC2 machine; exact sizing and hosting remain a later decision. Dashboard/daemon may move onto a larger VM to reduce laptop load. Oracle free-tier eligibility and pay-as-you-go charges must be checked against the actual account and provisioning settings before creating resources; no guaranteed-free assumption.

## Phase 3 — quota-aware orchestration

Route repetitive extraction, normalization, counting, checks and long-running bounded work toward capable remote workers. Use stronger cloud models for ambiguous reasoning, creative work and review. Scheduling considers task requirements, measured worker quality, quota/cost, concurrency, dependencies, latency and data privacy. Preserve safety reserves, explicit budget ceilings, deterministic assignments and a single owner. More slots are useful only when independent work exists.

LightSprint MCP naming convention: lightsprint-N-username, currently nine configured accounts. Private usernames belong in local configuration, not this public document. These are configuration labels, not authenticated identity evidence. Account 1 is reported depleted this month; account 2 may be depleted; verify the rest. Monthly refresh does not imply a known reset timestamp. Display occupied rows only. Default 12 maximum reservations per account; higher limits require provider/model/account confirmation.

## Phase 4 — universal integrations

A shared adapter contract avoids hardcoding every possible website into the scheduler. Each adapter advertises supported capabilities: identity, quota, capacity, launch, observe, resume, cancel, artifacts, tools and notifications. Unsupported operations remain unavailable. Provide HTTP/CLI and MCP interfaces so CLI and GUI agents can integrate where their products permit it. No universal arbitrary-chat injection claim.

Planned adapters: LightSprint, local OpenCode, registered local agents, SSH/Tailscale worker services, Ollama, and other user-selected cloud providers. Add least-privilege worker tool configuration for Mem0, Exa/search, Firecrawl and spreadsheet tools. Separate per-project Mem0 continuity from credentials and raw logs. Workers receive only needed tools and scoped data.

## Phase 5 — design agents

Reserve an optional adapter category for v0.app and Figma/Figma Make. Investigate official APIs/MCPs and permitted account workflows first. A ChatGPT Figma connector is not automatically a headless Figma Make orchestration API. Browser automation on a VM is an optional later experiment requiring secure authentication, product permission and actual execution proof; it is not a promised capability. Avoid spending quota or keeping remote browsers alive by default.

## Open-source reuse research

Symphony: https://github.com/openai/symphony — inspected observability API, presenter and selected orchestration code. Apache-2.0; candidate patterns include human-readable running/retrying/blocked snapshots and bounded scheduling. Do not require its Elixir runtime in the small version.

AgentOps: https://github.com/AgentOps-AI/agentops — SDK and app have distinct licensing; inspected app/LICENSE is Elastic License 2.0. Do not assume an MIT SDK licenses its dashboard for unrestricted reuse.

Langfuse: https://github.com/langfuse/langfuse — candidate later tracing/evaluation integration, not a prerequisite for fleet scheduling. Check exact module license and infrastructure footprint before reuse.

Dagster: https://github.com/dagster-io/dagster — candidate scheduling/state concepts; not adopted for this first version. Inspect exact modules and license if reusing source.

Every copied module must record upstream URL, pinned revision, license and modifications. Open-source ambition does not remove license restrictions. Prefer tested reusable modules over wholesale platform combinations.

## Instructions for the next AI coordinator

Read the first-version spec and current repo/tests before changes. Recheck configured accounts and provider evidence; never infer working sessions from launch acknowledgements. Keep expensive native work minimal and explicitly justified. Do not deploy the entire roadmap while Trump Files remains unfinished. Keep source-supported facts, internal drafts and publication readiness separate. Save Snooze memories under user JQ and app snooze; do not mix its roadmap into the Trump Files namespace.
