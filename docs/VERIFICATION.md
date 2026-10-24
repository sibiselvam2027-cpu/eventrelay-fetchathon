# Verification record

Local verification on 24 October 2026 used Python 3.12.14, uAgents 0.25.5, uAgents Core 0.4.12 and Pydantic 2.14.1.

**65 tests passed** before the initial repository publication. The five generated hosted projects also passed Python compilation. The scripted end-to-end scenario passed seven workflow assertions.

Coverage includes clarification before dispatch, offer versus acceptance, backup routing, timeouts and escalation, roster availability changes, concurrent staff reservation, stale versions, replay protection, linked prerequisites, completion versus closure, reporter authorization, reopening, persistent transport routing and retries, and native card metadata.

Hosted-specific tests reconstruct a new invocation and reload Agent Storage between steps through report, decline, backup offer, acceptance, work start, completion and reporter-confirmed closure. They check that state is checkpointed before outbound sends.

These are local tests using actual uAgents model/protocol classes and a fake hosted execution context. They do not establish Agentverse execution, live ASI1 API success, ASI:One discoverability, actual staff participation or physical resolution. Each of those requires a separate live check.

Hosted state uses one sequential coordinator writer. No distributed compare-and-swap guarantee is claimed for Agent Storage.
