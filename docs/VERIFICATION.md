# Verification record

Local verification on 24 October 2026 used Python 3.12.14, uAgents 0.25.5, uAgents Core 0.4.12 and Pydantic 2.14.1.

**65 tests passed** before the initial repository publication. The five generated hosted projects also passed Python compilation. The scripted end-to-end scenario passed seven workflow assertions.

The initial public commit `6a67685ed784b8dfa88aa67da31facddeb13c133` also passed [GitHub Actions](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40083719828), with 65 tests confirmed in the CI job log.

The current source revision adds hosted SDK/schema and ASI endpoint/credential handling fixes. **68 tests passed locally** for this revision. CI for the updated source must be checked against its new published commit; the earlier 65-test CI result does not verify these subsequent changes.

Coverage includes clarification before dispatch, offer versus acceptance, backup routing, timeouts and escalation, roster availability changes, concurrent staff reservation, stale versions, replay protection, linked prerequisites, completion versus closure, reporter authorization, reopening, persistent transport routing and retries, and native card metadata.

Hosted-specific tests reconstruct a new invocation and reload Agent Storage between steps through report, decline, backup offer, acceptance, work start, completion and reporter-confirmed closure. They check that state is checkpointed before outbound sends.

These are local tests using actual uAgents model/protocol classes and a fake hosted execution context. They do not establish Agentverse execution, live ASI1 API success, ASI:One discoverability, actual staff participation or physical resolution. Each of those requires a separate live check.

All five hosted identities have now been created. Coordinator execution logs show startup, Almanac registration, and interval handlers starting. Those observations establish provisioning and coordinator startup, not a completed five-agent ASI:One workflow. Public profile accessibility, natural-language ASI1 execution, discovery, and a complete shared-chat demonstration remain separate checks.

Hosted state uses one sequential coordinator writer. No distributed compare-and-swap guarantee is claimed for Agent Storage.
