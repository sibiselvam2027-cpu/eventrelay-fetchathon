# Verification record

**Current published source baseline: 74 tests passed locally and in [GitHub Actions](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40089811983), source commit `c5f0c8d5882f01b055f8b52337a638c8d109d243`.** Hosted builds/compilation and the synthetic scenario also passed. Actual hosted rehearsals closed four synthetic service categories and exercised same-ID reopening plus one natural-language status lookup. Full ASI:One UI completion remains pending. The entries below preserve the verification history and its limits.

Local verification on 24 October 2026 used Python 3.12.14, uAgents 0.25.5, uAgents Core 0.4.12 and Pydantic 2.14.1.

**65 tests passed** before the initial repository publication. The five generated hosted projects also passed Python compilation. The scripted end-to-end scenario passed seven workflow assertions.

The initial public commit `6a67685ed784b8dfa88aa67da31facddeb13c133` also passed [GitHub Actions](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40083719828), with 65 tests confirmed in the CI job log.

Published commit `1a2297db3d45e9799fd0b34bb28e92a14ec8ce1b` adds hosted SDK/schema and ASI endpoint/credential handling fixes. **68 tests passed locally and in [GitHub Actions](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40084970945)**. CI also built/compiled all five hosted projects and passed the complete synthetic scenario. That run finished at 15:42:33 IST. A subsequent ASI SDK client revision is under verification; the 68-test result does not automatically cover later edits.

Coverage includes clarification before dispatch, offer versus acceptance, backup routing, timeouts and escalation, roster availability changes, concurrent staff reservation, stale versions, replay protection, linked prerequisites, completion versus closure, reporter authorization, reopening, persistent transport routing and retries, and native card metadata.

Hosted-specific tests reconstruct a new invocation and reload Agent Storage between steps through report, decline, backup offer, acceptance, work start, completion and reporter-confirmed closure. They check that state is checkpointed before outbound sends.

These are local tests using actual uAgents model/protocol classes and a fake hosted execution context. They do not establish Agentverse execution, live ASI1 API success, ASI:One discoverability, actual staff participation or physical resolution. Each of those requires a separate live check.

All five hosted identities have been created, and retrieved cloud logs show successful startup and registration for each agent. Coordinator interval handlers also continued executing. [Live deployment record](LIVE_DEPLOYMENT.md)

At approximately 15:40 IST, ASI:One reached the coordinator and displayed its actual response. This verifies an ACP request/reply path. That response reported an ASI1 authentication error and did not verify natural-language reasoning. Later ASI:One frontend 503/504 errors affected websocket/history requests and follow-up sends stalled. The later hosted rehearsals below establish a separate multi-agent workflow and successful status lookup; the full ASI:One UI workflow and public shared chat remain pending.

Hosted state uses one sequential coordinator writer. No distributed compare-and-swap guarantee is claimed for Agent Storage.

Published SDK-client/guided-recovery commit `9822b8c309f4b0fd53ae3cbef96e88614f124932` passed **69 local tests and 69 tests in [GitHub Actions](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40085835961)**, rebuilt all five hosted projects, and passed Python compilation. CI finished at 15:55:36 IST. It uses the OpenAI-compatible SDK client and includes an explicitly labelled manual guided-form recovery when ASI1 requests fail. Recovery creates no issue or offer until the user supplies the required details through ASI:One. Tests cover avoiding accidental reuse of an older pending report. This is availability recovery, not proof that ASI1 authentication or natural-language reasoning is fixed. Live recovery-form rendering remains pending, and later timeout-budget changes require separate verification.

Bounded-wait commit `532a5a7f1746d8408adff23f06ba42f01fafb124` also passed [CI](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40086061325). A further regression verifies that acknowledgment and LLM timeouts still return only a manual form without creating an issue or offer. The current full local suite passed **70 tests**. CI for the newly published test revision must be checked separately.

## Negative live observer result

Agentverse confirmed dispatch of a natural-language report at approximately 15:52:10 IST and structured reports at 15:53:49 and 15:56:17. No response callbacks reached the temporary diagnostic observer before it stopped, and execution timeouts appeared in the retrieved logs. These observations do **not** establish live vendor acceptance, closure, or an ASI:One end-to-end workflow.

The disposable observer and failed-deployment orphan were removed after exact-ID checks. The cleanup inventory contained the five product roles, compiled and running. Diagnostic agents are not part of EventRelay's five-agent architecture or submission. Later control tests and the native-form recovery must be assessed separately from that earlier negative result.

## Windows configuration and persisted-route normalization

Live logs exposed a concrete peer-dispatch fault: configuration values included trailing carriage-return characters from Windows CRLF environment files. The current revision strips public peer addresses and model/configuration values, emits generated environment files with LF endings, and normalizes previously persisted peer routes without resetting the existing event or issue records. A full contaminated-configuration regression covers report, decline, backup acceptance, completion, and confirmation; another regression preserves an existing issue version and its original reporter route during migration.

The configuration/migration source commit `8896fbb2dc0f934e593f509752859912437471f0` passed **73 tests locally and in [CI](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40087069509)**. Hosted build/compile and the synthetic scenario also passed. A separate minimal control agent failed to start a chat while ASI frontend 503 errors were observed. Source tests and that frontend observation do not establish the complete ASI:One UI workflow; the later structured-message rehearsal is recorded below.

## Positive structured-message hosted rehearsal

After the configuration fix, actual hosted coordinator/hospitality transport carried synthetic issue ER-A50BFBB4 through offered v2, backup offered v4, Neha accepted v5, in progress v6, awaiting confirmation v7, and closure at **16:16:19 IST** in the same ACP session. The hospitality agent supplied its configured synthetic primary-decline/backup-accept decisions; the observer never clicked Accept. Progress, physical work, and reporter confirmation were explicitly simulated. [Sanitized proof](LIVE_WORKFLOW_PROOF.md)

This establishes the tested hosted orchestration and persistent lifecycle for that category. It supersedes the earlier routing-failure limitation for this structured-message path. It does not establish ASI:One frontend availability, LLM extraction, a public shared chat, or real-world service completion.

## Additional service categories and natural-language status lookup

By **16:25:07 IST**, a further hosted rehearsal observed audio `ER-3B225E95`, power `ER-CB20232F`, and cleanup `ER-5C25C933` reach closure. Audio first reached awaiting confirmation, reopened under the same ID, reaccepted, and then closed. Actual vendor agents supplied their configured synthetic accept decisions. Diagnostic actions simulated crew progress, physical work, and reporter confirmation. [Recorded states and scope](LIVE_WORKFLOW_PROOF.md)

The plain-language request “show status of ER-A50BFBB4” returned the actual stored closed water issue through the hosted ASI1 extraction path without the earlier authentication error. This is evidence for that natural-language status lookup. It does not establish the complete natural-language report/clarification path or ASI:One frontend completion. Shared chat, video, live native-form rendering, and real service delivery remain unverified.

## Final transport and safe diagnostic revision

The final source preserves the SDK's normal 30-second envelope lifetime while retaining independent local acknowledgment/final-send wait budgets of 2/4 seconds. A regression checks both values separately. Safe diagnostics record whether a key is present and a known model name or `[custom]`; no credential or arbitrary model-setting value is logged. **74 tests passed locally and in [CI](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40089811983)** for source commit `c5f0c8d5882f01b055f8b52337a638c8d109d243`; all five hosted builds/compilation and the synthetic scenario also passed. CI completed at approximately 16:55:33 IST.

At the final frontend check, an ASI:One attempt still failed to start and another browser attempt remained loading. These are observed attempt failures, not a claim of a platform-wide outage. A completed public shared chat, 3–5 minute demo video, and actual competition submission are not yet available.

## Later organizer announcement supplied to the team

The team received an organizer announcement reporting ASI:One downtime, extending submission until **11:59 PM IST on 24 October 2026**, and recommending Agentverse **Agent Profile → Testing → Manual Testing** for demonstrations. This is recorded as a supplied organizer statement; it is not an independent service-wide status measurement. The screenshot, organizer identity, and private contact information are not published here.

Manual Testing rehearsal and recording are the next evidence items. Their results must be recorded separately from ASI:One UI completion and public shared-chat availability, which remain pending recovery. The stable source and 74-test verification are unchanged by this documentation update.
