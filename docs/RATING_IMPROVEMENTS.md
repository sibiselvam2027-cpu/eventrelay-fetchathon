# Coordinator quality review

Review date: **27 October 2026, IST**. This records observed results separately from proposed improvements. It does not claim a 4.5 rating or guarantee a future score.

## Baseline

The coordinator profile displayed a **3.4/5 rating**, **100% uptime**, and **23.2K interactions** before this review. Agentverse defines the displayed uptime as the percentage of requests answered in the last 30 days. These are platform observations, not evidence of real event work or independently validated users.

The first automated run used five platform-generated questions and scored **60%: 3 of 5 passed**. Its overall **Passed** label indicated that the evaluation run completed; it did not mean all five questions passed.

Two questions failed: a contextual request to escalate an unresponsive crew received generic command help, and a question asking how to confirm a restored water supply repeatedly received an unrelated new-report form after ASI1 failures.

Case 3 also exposed a misleading evaluator success: a request for all open issues, followed by an invalid issue reference, eventually created a new synthetic report. That was not a successful status lookup. The original implementation only supported individual lookups; this review added an authorized, read-only open-issue overview.

## Changes and safeguards

- Published a **4,685-character coordinator README** with supported categories/locations, inputs and outputs, the five-agent workflow, synthetic crew behavior, original-session confirmation, the overview and current limitations. Both required badges remain. The build script now preserves customized hosted READMEs.
- Added bounded, deterministic answers for product scope, confirmation instructions and escalation questions. These return guidance only: they **do not force escalation, mark work complete or close an issue**.
- Invalid `ER-` references now receive format guidance instead of becoming new reports. Confirmation still requires the original reporter or configured organizer and the correct issue state.
- Clarification enriches the original complaint without discarding it. Native form selections, stale-form checks, length bounds and sender-derived permissions remain enforced.
- Added an overview of up to 20 actual open issues. Permission filtering precedes both the limit and count. The overview neither dispatches offers nor changes issue or conversation state. Escalation requests without a reference show actual visible choices instead of inventing an issue. A standalone valid reference uses the existing authorized status lookup.
- **102 local tests passed**, covering the added behavior and existing workflow, identity, replay, storage and transport checks. This test count is separate from platform evaluation results.

## Deployment verification

Only the three reviewed coordinator files—`router.py`, `fetch_agents.py` and `hosted_runtime.py`—were updated through the owner interface. Saved source was read back and all three hashes matched the staged files. Startup logs showed a healthy restart at **00:27:19 IST**. The final overview refinement then changed only `router.py`, with saved-source readback and another successful restart. It required no new dependency, schema or credential.

The previously verified public incident **ER-4DE240CA** remained **closed**, with **Ravi** as accountable owner. A controlled facilities regression, **ER-02125351**, used structured report input, actual Facilities-agent acceptance by synthetic worker Pooja, native Start/Done, and native original-reporter confirmation to reach **closed**. This proves the structured workflow, not a new natural-language report interpretation. ASI:One also delivered the new confirmation instructions in a fresh chat; a transient reCAPTCHA connection alert appeared while that page loaded, but the agent reply was ultimately observed.

All five agents were active after the update. The four specialist deployments were untouched. No secrets or agent identities changed, no stored issue state was reset, and no authorization rule was weakened.

## Post-change platform evaluation

Three automated evaluations used the **same five question texts with the same blank optional expected-answer fields**. No failed run was deleted and no grading fields were edited.

| Run | Score | Observed result |
|---|---|---|
| Original baseline | 60%, 3/5 | Confirmation guidance and escalation request failed. The all-issues case received a misleading pass after an unrelated report was created. |
| Guidance/reference/clarification update | 60%, 3/5 | Confirmation guidance passed. The reference guard correctly rejected a six-character ID, which the grader incorrectly described as a valid eight-character ID. A no-reference escalation request still failed. |
| Final read-only overview update | 60%, 3/5 | Open-issue status and confirmation guidance passed. Cleanup coordination with no available crew and the unspecified escalation request failed. The latest overall label was **Needs work**. |

The final cleanup case recorded **ER-C3BED37E** and honestly escalated it because no eligible cleanup crew was available. The grader suggested claiming dispatch and removing the demo disclosure; those suggestions were not applied. The unspecified escalation case showed actual visible issue choices and requested a target reference, rather than escalating an arbitrary incident. Those are remaining evaluation mismatches and product limitations, not evidence that all five scenarios passed.

The displayed coordinator rating was subsequently observed at **3.6/5**, compared with **3.4/5** before the review. This is a platform observation, not proof that any one edit caused the increase or a guarantee of 4.5. The automatic evaluation remains **60%** and must not be represented as a 4.5 rating or a 100% pass.

No fake interactions, ratings or real-world repair claims were introduced. Synthetic evaluation reports may affect the persistent demo roster; they must not be presented as serviced events.
