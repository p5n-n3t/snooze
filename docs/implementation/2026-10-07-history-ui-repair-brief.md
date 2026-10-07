# History UI review repairs

Continue your existing isolated History UI task branch. Own exactly the new History components/helper/types/tests/report from the original brief; no App/global CSS/assets or Python changes. Fetch newest coordinator producer/contracts; merge if needed, never force-push or overwrite other workers.

Two Important review defects must be repaired before root integration:

1. The account/model/effort option domains derive from the actively filtered report. Selecting one option removes the remaining options on the next response, so the user cannot add another. Keep a stable independently fetched unfiltered option domain (bounded same-project/date/timezone query), or retain the original complete domain across narrowed responses, including selected values. Reset appropriately for project/date/timezone context changes. Do not label a truncated domain complete or issue an unlimited second query. Add a regression: start with accounts A/B, select A, receive narrowed A response, and still select B without clearing A; test model/effort as well.
2. Client state accepts 24 repeated filter values but the backend contract allows 20. Align at 20 through URL restore, UI selection and serialization; meaningful tests for 20 accepted and 21 rejected/capped consistently. No silently submitting a known-invalid request.

Add RED regressions then fix, run npm test/check/build, append repair evidence to the existing worker report, commit only owned files and push. Existing draft PR can update; PR creation/publishing is already approved. No screenshots claim unless actually rendered; root owns App integration and final browser proof. No provider tasks/subagents/other repositories/Neon.
