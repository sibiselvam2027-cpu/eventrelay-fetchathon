# EventRelay agent quality review

Review date: **27 October 2026, IST**. This records observed results separately from proposed improvements. It does not claim a 4.5 rating or guarantee a future score.

## Baseline

The coordinator profile displayed a **3.4/5 rating**, **100% uptime**, and **23.2K interactions** before this review. Agentverse defines the displayed uptime as the percentage of requests answered in the last 30 days. These are platform observations, not evidence of real event work or independently validated users.

The first automated run used five platform-generated questions and scored **60%: 3 of 5 passed**. Its overall **Passed** label indicated that the evaluation run completed; it did not mean all five questions passed.

Two questions failed: a contextual request to escalate an unresponsive crew received generic command help, and a question asking how to confirm a restored water supply repeatedly received an unrelated new-report form after ASI1 failures.

Case 3 also exposed a misleading evaluator success: a request for all open issues, followed by an invalid issue reference, eventually created a new synthetic report. That was not a successful status lookup. The original implementation only supported individual lookups; this review added an authorized, read-only open-issue overview.

## Phase-one changes and safeguards

- Published a **4,685-character coordinator README** with supported categories/locations, inputs and outputs, the five-agent workflow, synthetic crew behavior, original-session confirmation, the overview and current limitations. Both required badges remain. The build script now preserves customized hosted READMEs.
- Added bounded, deterministic answers for product scope, confirmation instructions and escalation questions. These return guidance only: they **do not force escalation, mark work complete or close an issue**.
- Invalid `ER-` references now receive format guidance instead of becoming new reports. Confirmation still requires the original reporter or configured organizer and the correct issue state.
- Clarification enriches the original complaint without discarding it. Native form selections, stale-form checks, length bounds and sender-derived permissions remain enforced.
- Added an overview of up to 20 actual open issues. Permission filtering precedes both the limit and count. The overview neither dispatches offers nor changes issue or conversation state. Escalation requests without a reference show actual visible choices instead of inventing an issue. A standalone valid reference uses the existing authorized status lookup.
- **102 local tests passed**, covering the added behavior and existing workflow, identity, replay, storage and transport checks. This test count is separate from platform evaluation results.

## Phase-one deployment verification

Only the three reviewed coordinator files—`router.py`, `fetch_agents.py` and `hosted_runtime.py`—were updated through the owner interface. Saved source was read back and all three hashes matched the staged files. Startup logs showed a healthy restart at **00:27:19 IST**. The final overview refinement then changed only `router.py`, with saved-source readback and another successful restart. It required no new dependency, schema or credential.

The previously verified public incident **ER-4DE240CA** remained **closed**, with **Ravi** as accountable owner. A controlled facilities regression, **ER-02125351**, used structured report input, actual Facilities-agent acceptance by synthetic worker Pooja, native Start/Done, and native original-reporter confirmation to reach **closed**. This proves the structured workflow, not a new natural-language report interpretation. ASI:One also delivered the new confirmation instructions in a fresh chat; a transient reCAPTCHA connection alert appeared while that page loaded, but the agent reply was ultimately observed.

All five agents were active after the update. The four specialist deployments were untouched. No secrets or agent identities changed, no stored issue state was reset, and no authorization rule was weakened.

## Phase-one platform evaluation

Three automated evaluations used the **same five question texts with the same blank optional expected-answer fields**. No failed run was deleted and no grading fields were edited.

| Run | Score | Observed result |
|---|---|---|
| Original baseline | 60%, 3/5 | Confirmation guidance and escalation request failed. The all-issues case received a misleading pass after an unrelated report was created. |
| Guidance/reference/clarification update | 60%, 3/5 | Confirmation guidance passed. The reference guard correctly rejected a six-character ID, which the grader incorrectly described as a valid eight-character ID. A no-reference escalation request still failed. |
| Final read-only overview update | 60%, 3/5 | Open-issue status and confirmation guidance passed. Cleanup coordination with no available crew and the unspecified escalation request failed. The latest overall label was **Needs work**. |

The final cleanup case recorded **ER-C3BED37E** and honestly escalated it because no eligible cleanup crew was available. The grader suggested claiming dispatch and removing the demo disclosure; those suggestions were not applied. The unspecified escalation case showed actual visible issue choices and requested a target reference, rather than escalating an arbitrary incident. Those are remaining evaluation mismatches and product limitations, not evidence that all five scenarios passed.

The displayed coordinator rating was subsequently observed at **3.6/5**, compared with **3.4/5** before the review. This is a platform observation, not proof that any one edit caused the increase or a guarantee of 4.5. The automatic evaluation remains **60%** and must not be represented as a 4.5 rating or a 100% pass.

No fake interactions, ratings or real-world repair claims were introduced. Synthetic evaluation reports may affect the persistent demo roster; they must not be presented as serviced events.

## Phase two: specialist guidance and real review requests

The initial combined local suite passed **123 tests**; the coordinator refinements then passed 128. The final combined source suite passes **144 tests in 6.108 seconds**, including specialist FAQs, worker authentication, review authorization, replay protection and the storage regression fixes described below. All five hosted builds also compiled successfully. Source tests, live Agentverse evaluations and profile ratings are separate evidence.

- **Four public specialist guides:** Hospitality explains drinking-water coordination; Audio explains microphone/speaker coordination; Facilities explains power/lighting coordination; Housekeeping explains spill/cleanup coordination. Each provides the actual coordinator link and a sample report. Static guidance reads no private event state, inbox, staff mapping or ASI credential and calls no model. It explicitly does not forward the message, create an issue, assign crew or report work complete. Worker commands still require an authenticated sender and a matching trusted coordinator offer.
- **Explicit review requests with a known issue:** only the original reporter or configured organizer can record organizer review, even in demo mode. The exact target reference must appear in the caller's message or native JSON; an ASI guess cannot select an owned or visible issue. Review metadata and activity history change, while crew ownership, operational status, offer version and deadlines remain intact. No crew reassignment, completion, closure or human notification is claimed.
- **Explicit requests without an issue reference:** create an actor-owned, unlinked **RV-XXXXXXXX** review item with `queued` status. The system does not guess an incident or silently use the last issue. Repeated delivery of the same message ID reuses the request; conflicting reuse is rejected. Notes are bounded, each conversation has at most 20 queued items, and existing clarification/last-issue state is preserved. These items persist through the existing conversation storage.
- **Read access:** `my review requests` lists only that authenticated conversation's items. `organizer review queue` requires the configured organizer identity, including in demo mode. Claiming to be an organizer in text or JSON grants no access. Questions such as “How do I escalate?” remain instructions only and create no request.
- **Honest capacity responses:** an unavailable category is explained in plain language, with the actual unowned/escalated state. The system does not invent acceptance or suppress the synthetic-demo disclosure to satisfy a grader.

## Initial phase-two deployment and live checks

All five agents received coherent seven-module builds through the signed-in Agentverse interface, one agent at a time. Every saved module was read back and matched the staged source before restart. All five initial deployments showed healthy startup and were subsequently observed **Active**. No new credential, database schema or issue-state reset was required. Final refinement deployment is recorded separately below.

A new controlled incident, **ER-A8B0154D**, reported a **Power / facilities** problem at the **Entrance**. The actual Facilities agent returned acceptance for synthetic crew member **Pooja**. A native **Request organizer review** action preserved the accepted owner, operational status and offer version. Native **Start** then advanced the same issue to **in progress**. A later rehearsal exposed a state rollback before the storage guard was installed, so this partial sequence alone was not treated as persistence proof. Review is recorded for organizer attention, without claiming a human notification was sent or acted on.

## Initial phase-two platform outcomes

The coordinator retained the original five question texts and blank optional expected-answer fields. Each specialist used five platform-generated questions derived from its published scope, also with blank expected-answer fields. All generated texts and initial failed results were retained unchanged; no failed history was deleted.

| Agent | Displayed rating before phase two → observed after initial checks | Initial phase-two platform evaluation | Observation |
|---|---|---|---|
| Coordinator | 3.6 → **3.7/5** | **40%, 2/5 passed** | Main Stage clarification loop, no-reference escalation response and unavailable cleanup capacity failed; status overview and confirmation guidance passed. |
| Hospitality | 2.0 → **2.2/5** | **20%, 1/5 passed** | Initial public-guide evaluation; failures retained for review. |
| Audio | 1.7 → **2.1/5** | **40%, 2/5 passed** | Initial public-guide evaluation; failures retained for review. |
| Facilities | 1.4 → **2.0/5** | **40%, 2/5 passed** | Initial public-guide evaluation; failures retained for review. |
| Housekeeping | 1.0 → **1.8/5** | **40%, 2/5 passed** | Location and crew-response instructions passed; new dispatch, cross-category refill and physical-cleanup confirmation replies failed. |

These displayed ratings are platform observations. The timing does not establish that any particular code change, profile edit or evaluation caused an increase. **No agent has been observed at 4.5/5**, and an evaluation percentage is not a profile rating.

The coordinator's first phase-two evaluation exposed a real location-normalization bug: both the original report and a follow-up naming **Main Stage** repeatedly received a location question. A bounded alias correction now maps that known venue label to **Stage** and is deployed. It still rejects unregistered locations. The initial no-reference escalation reply did create a real queued **RV-** request, but appended a long list of unrelated demo issues; that automatic list is now removed and the response more directly acknowledges the reported concern. Cleanup with no available eligible crew remains honestly escalated and unowned. No fabricated dispatch, acceptance, physical repair or human notification was added to satisfy those cases.

The specialist evaluations also exposed overly broad replies: the first guide returned a long general explanation even when the caller asked about an existing issue or closing a report. Deployed FAQs now distinguish reporting, locations, crew instructions, status checks and reporter confirmation. Existing-issue questions use the authorized coordinator lookup instead of instructions to create a new report. Public guidance preserves trusted crew authentication and does not claim that a report was forwarded or a repair was verified.

## Storage rollback regression and limits

A live rehearsal displayed an earlier **accepted** state after a **Start** transition. A focused regression reproduced the underlying failure pattern: an older read-only session opened accepted version 3, a writer saved in-progress version 4, and the older session's checkpoint overwrote it with version 3. This was a real defect to fix, not a result to hide or bypass by resetting incidents.

The updated storage adapter skips unchanged snapshots and rejects a changed session when the current stored baseline visibly differs from the one it opened. The runtime checkpoints domain state before saving transport claims or sending crew operations. An unchanged transport save also skips the write, preventing that no-op from flushing a cached whole-storage dictionary over a newer domain snapshot. Checkpoint rejection returns safe retry guidance instead of an AI fallback, a new report form or a crew operation. Existing address-format migration still saves an actual change once. These behaviors have regression coverage within the 144-test suite.

This remains a **single coordinator writer** design. The baseline check depends on `storage.get` exposing the latest stored value; it is **not distributed compare-and-swap**, a cross-worker transaction or a guarantee against every cached-backend race. No credentials, identities, storage schema or existing incidents were reset to apply the fix.

## Final refinement deployment and evaluations

All five final seven-module builds, including the runtime and storage guards, were saved through Agentverse. Every saved module exactly matched staged-source readback and all five agents restarted successfully. The same question texts and blank optional expected-answer fields were retained for the final evaluations.

| Agent | Final refinement deployment/readback | Final platform retest | Change from initial phase-two run | Final displayed rating |
|---|---|---|---|---|
| Coordinator | Seven modules matched; restarted | **80%, 4/5 passed** | +40 percentage points | **3.7/5** |
| Hospitality | Seven modules matched; restarted | **40%, 2/5 passed** | +20 percentage points | **2.4/5** |
| Audio | Seven modules matched; restarted | **40%, 2/5 passed** | Unchanged | **2.3/5** |
| Facilities | Seven modules matched; restarted | **60%, 3/5 passed** | +20 percentage points | **2.2/5** |
| Housekeeping | Seven modules matched; restarted | **40%, 2/5 passed** | Unchanged | **2.1/5** |

A fresh My Agents view showed all five **Active** with the final ratings above. Relative to the phase-two baselines, the displayed ratings changed **3.6 → 3.7**, **2.0 → 2.4**, **1.7 → 2.3**, **1.4 → 2.2** and **1.0 → 2.1**, respectively. The same view showed **29.3K**, **40**, **33**, **29** and **24 interactions**. Those are platform interaction counts, not distinct users or serviced events. The observations do not establish which change caused a rating increase, and every displayed rating remains below 4.5.

The coordinator's only remaining failed question asks to escalate an unspecified incident without an issue reference. EventRelay records a real queued **RV-** review request and asks for context instead of selecting an unrelated issue or claiming a human notification. The remaining specialist failures request dispatch, physical confirmation or closure without the required authenticated context. Those capabilities were not fabricated or granted to unauthenticated public chats to increase the score. Initial failed runs remain in the history.

After the storage guard deployment, a fresh status read showed **ER-A8B0154D in progress**. Native **Done** advanced it to **awaiting confirmation**, and the **original reporter's Yes, resolved** closed it at **10:21 IST on 27 October 2026**. A fresh status read at **10:22 IST** still showed **closed**. The older public **ER-4DE240CA** audio incident remained **closed**, with **Ravi** as owner. Staff decisions and physical work remain synthetic. These observations establish the recorded pre-restart completion and subsequent read, not physical electrical repair.

An additional controlled **Stop / Start of the coordinator**, without source edits or a state reset, was then completed. A new status reply at **10:23 IST** again showed **ER-A8B0154D closed**, **Pooja** as owner and the retained activity history. This verifies persistence across that specific restart and subsequent lookup; it does not remove the single-writer or cached-backend limitations described above.

The earlier **60% coordinator evaluations** remain historical phase-one observations. Retain original question texts, blank expected-answer settings and failed results when comparing the final runs. The recorded rating increases do not establish a 4.5 achievement or a guarantee of a future score.
