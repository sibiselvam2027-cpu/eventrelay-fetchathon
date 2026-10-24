# Verification record

Local verification on 24 October 2026 used Python 3.12.14, uAgents 0.25.5, uAgents Core 0.4.12 and Pydantic 2.14.1.

**65 tests passed** before the initial repository publication. The five generated hosted projects also passed Python compilation. The scripted end-to-end scenario passed seven workflow assertions.

The initial public commit `6a67685ed784b8dfa88aa67da31facddeb13c133` also passed [GitHub Actions](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40083719828), with 65 tests confirmed in the CI job log.

Published commit `1a2297db3d45e9799fd0b34bb28e92a14ec8ce1b` adds hosted SDK/schema and ASI endpoint/credential handling fixes. **68 tests passed locally and in [GitHub Actions](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40084970945)**. CI also built/compiled all five hosted projects and passed the complete synthetic scenario. That run finished at 15:42:33 IST. A subsequent ASI SDK client revision is under verification; the 68-test result does not automatically cover later edits.

Coverage includes clarification before dispatch, offer versus acceptance, backup routing, timeouts and escalation, roster availability changes, concurrent staff reservation, stale versions, replay protection, linked prerequisites, completion versus closure, reporter authorization, reopening, persistent transport routing and retries, and native card metadata.

Hosted-specific tests reconstruct a new invocation and reload Agent Storage between steps through report, decline, backup offer, acceptance, work start, completion and reporter-confirmed closure. They check that state is checkpointed before outbound sends.

These are local tests using actual uAgents model/protocol classes and a fake hosted execution context. They do not establish Agentverse execution, live ASI1 API success, ASI:One discoverability, actual staff participation or physical resolution. Each of those requires a separate live check.

All five hosted identities have been created, and retrieved cloud logs show successful startup and registration for each agent. Coordinator interval handlers also continued executing. [Live deployment record](LIVE_DEPLOYMENT.md)

At approximately 15:40 IST, ASI:One reached the coordinator and displayed its actual response. This verifies an ACP request/reply path. The response reported an ASI1 authentication error; it does not verify natural-language reasoning or a complete issue workflow. Later ASI:One frontend 503/504 errors affected websocket/history requests and follow-up sends stalled. No completed live multi-agent demonstration, public shared chat, or successful authentication repair is claimed while those checks remain pending.

Hosted state uses one sequential coordinator writer. No distributed compare-and-swap guarantee is claimed for Agent Storage.

The final source revision passed **69 local tests**, rebuilt all five hosted projects, and passed Python compilation. It uses the OpenAI-compatible SDK client and includes an explicitly labelled manual guided-form recovery when ASI1 requests fail. Recovery creates no issue or offer until the user supplies the required details through ASI:One. Tests cover avoiding accidental reuse of an older pending report. This is availability recovery, not proof that ASI1 authentication or natural-language reasoning is fixed. Live recovery-form rendering and CI for this final revision remain pending.
