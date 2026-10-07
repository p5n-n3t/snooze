# LightSprint continuation contract: live correction

The configured MCP's published `/api/agent-sessions/{sessionId}/chat` example on 2026-10-07 used `{"content":"..."}`. Actual requests returned **HTTP 400: message is required**. A request with `message` alone returned **HTTP 400: clientMessageId is required**. Both were rejected, not accepted continuations.

The working body is `{"message":"...","clientMessageId":"persisted-unique-UUID"}`. A bounded UI follow-up returned `ok:true,queued:true` with a durable queue item; the idle review session returned `ok:true,queued:false`. Neither response proves completed work; status/activity and pushed artifacts must still be checked.

Snooze now persists a separate message ID for each bounded recovery before network I/O and sends that exact ID. A restart cannot invent a new ID and duplicate an uncertain accepted continuation. Generic provider rejection used to obscure the actionability of this failure; bounded backend errors now retain a redacted rejection reason. Private API/UI receipts still do not expose raw provider error bodies.

Reproduction test: `tests.test_adapters.AdapterTests.test_resume_is_pending_not_completed` failed for the old `content` body, then failed for the missing ID, and passes for the confirmed body. The published tool example is stale; live first-party API validation is the evidence for this correction. The change does not globally enable resume/cancel or prove arbitrary provider idempotency lookup.
