# Live saved-output pipeline proof

2026-10-07, independent disposable state `/tmp/snooze-live-proof-n93erzkc`. This is a harmless arithmetic test, not a Trump Files entry or a Neon write. The existing production monitor was not taken over.

Snooze created an explicitly approved task `live-smoke-20261007` with exact record scope `smoke-1`, one configured LightSprint account, concurrency ceiling 1, model GPT-6 Luna and requested low effort. Unknown credits were allowed explicitly for this bounded test; no account balance was invented. Provider-confirmed effort remains unavailable.

1. Durable attempt `5e13f7bb80dd42e78f0a0d55f2fee244`, generation 1, reserved before network launch.
2. LightSprint accepted task `FlYlJslXvanNwwDyakEZu`, session `GsDrwkJBRLVbXfY7d7bES`, branch `ls/14-snooze-live-smoke-20261007-ZVkD`.
3. The worker saved and pushed the [result envelope](https://github.com/p5n-n3t/snooze/blob/ls/14-snooze-live-smoke-20261007-ZVkD/docs/implementation/smoke-results/live-smoke-20261007.json), with matching task, attempt, generation and `records=[{"id":"smoke-1","result":4}]`.
4. The configured read-only GitHub collector retrieved that exact repository/path/branch. Raw file SHA256: `1b03424c5628c22963a3f132fdc07da9a70710b5e60d120ad3ce14ce5ee2e7a7`; Git blob `0c664f4e845b0244e5b7578079e143c00eb3ebd0`.
5. Scheduler tick returned `validated_complete`, no errors; task is complete and its reservation is released. The exact-ID/required-field validator passed; the coordinator separately checked that the arithmetic result is 4.

The [GitHub Contents API](https://docs.github.com/en/rest/repos/contents#get-repository-content) provides the saved file with an explicit branch reference. Snooze does not treat provider idle, a PR receipt, or a raw runtime status as task completion.

This proves one real dispatch/collection/structural-validation path. It does not prove universal semantic correctness, automatic resume for every provider, broad session-usage ingestion, arbitrary GUI wakeups or production Trump Files ownership handover. Those remain distinct capabilities/release checks.
