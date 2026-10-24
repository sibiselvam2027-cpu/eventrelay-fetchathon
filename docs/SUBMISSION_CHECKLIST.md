# EventRelay — submission checklist

**Updated internal target: demo-ready by 16:45 IST, with a 17:00 rehearsal, 24 October 2026, as requested.** This is not an organizer-confirmed submission cutoff. The official page lists a 16:30 final-building/submission session but does not state an exact cutoff; check the current event announcement or dashboard. This checklist separates verified code evidence from live deployment and submission evidence.

## Verified code evidence

- [x] Public repository: [sibiselvam2027-cpu/eventrelay-fetchathon](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon).
- [x] Latest CI-verified published commit: `532a5a7f1746d8408adff23f06ba42f01fafb124`.
- [x] Initial local verification: **65 tests passed** before publication.
- [x] Published source fixes: **68 tests passed locally and in CI**.
- [x] SDK-client/guided-recovery source: **69 local and CI tests passed**; all five hosted projects rebuilt and compiled.
- [x] Additional timeout-recovery regression: current full local suite **70 tests — OK**. The new revision needs its own CI result.
- [x] GitHub Actions passed for that exact commit: [Verify EventRelay](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40086061325).
- [x] Its CI job passed workflow/persistence checks, hosted-project build/compile, and the complete synthetic scenario. [CI job](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40086061325/job/120849135298)

The bounded-wait source has passed CI. The subsequent 70th regression test and current documentation revision require their own CI result.

## Live hosted deployment

All five roles must run as Agentverse Hosted Agents. ASI:One is the sole product interface. The implementation uses direct uAgents/ACP and typed messages, with persistent Agent Storage.

| Hosted agent | Actual agent address | Public profile URL | Running and verified |
|---|---|---|---|
| Coordinator | `agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu` | Public access pending | Cloud startup, registration, intervals, and one ASI reply observed; full flow pending |
| Hospitality | `agent1qfrq6l9ta28f4xwn5twktttqns0fczgu3ueghkksrl900j6yl4v6ukxs3ng` | Public access pending | Cloud startup and registration observed; full flow pending |
| Audio | `agent1qga2l6uypaq0ks2sjl4e2jak650naa0dljznq5kxg34jfs2fsvjnq4da69d` | Public access pending | Cloud startup and registration observed; full flow pending |
| Facilities | `agent1qvxj23fgwdjncysveppxwmzx8yhx5rf9a6ssclxzk56ftj9gyfsgvxh8xkx` | Public access pending | Cloud startup and registration observed; full flow pending |
| Housekeeping | `agent1qgm0yx34j7qjcqnhjdpvftlwv295cdd0hlysrkqc0tp4zwxn70s0scfct3w` | Public access pending | Cloud startup and registration observed; full flow pending |

- [x] Five hosted identities created and their public addresses recorded.

- [x] Deploy and start all five hosted agents; retrieved cloud logs show successful starts and registration. See [LIVE_DEPLOYMENT.md](LIVE_DEPLOYMENT.md).
- [ ] Configure their actual cross-agent addresses and verify message exchanges.
- [ ] Configure ASI1 credentials in Agent Secrets; verify natural-language understanding without exposing the key.
- [ ] Verify issue, offer, conversation, and audit state across separate hosted invocations.
- [ ] Complete agent profiles and README information; verify ACP interaction and ASI:One discovery rather than assuming either from successful upload.

- [x] ASI:One reached the deployed coordinator and displayed an actual agent reply at approximately 15:40 IST. [Observed direct entry](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu)

That reply reported ASI1 authentication failure. Natural-language routing, successful resolution of that error, and the complete live workflow remain pending. Follow-up observation also encountered ASI:One frontend 503/504 errors and stalled sends.

The latest source offers an explicitly labelled manual guided form inside ASI:One when ASI1 is unavailable. It creates no issue or offer until the user submits the required details. Live form rendering and the final client revision must still be verified; this fallback is not evidence that the LLM authentication problem is fixed.

Temporary observer tests confirmed report dispatch but did not receive response callbacks before stopping. They provide no live acceptance, closure, or end-to-end proof. The disposable observer and failed-deployment orphan were cleaned up; diagnostic agents are not submitted product roles.

## Complete ASI:One proof — pending

- [ ] Report an ambiguous water issue; clarify it before dispatch.
- [ ] Show that an offered task has no accepted owner yet.
- [ ] Record a primary worker's decline and a backup's explicit acceptance.
- [ ] Show progress, worker-reported completion, and the awaiting-confirmation state.
- [ ] Reject an incomplete fix, reopen the same issue, then confirm the eventual resolution.
- [ ] Demonstrate a real timeout/escalation or a cross-team dependency that passed testing.
- [ ] Verify role restrictions and stale-action handling in the hosted flow.
- [ ] Create and open the **public ASI:One shared-chat URL**: Pending.

Keep demonstration people, configured responses, accelerated timers, and simulated physical work clearly labelled. A local test, protocol acknowledgment, or crew completion report is not proof of a real-world repair.

## Submission packet — pending

- [ ] Public repository URL and instructions to run/test the project.
- [ ] Five actual Agentverse profile URLs and agent addresses.
- [ ] Public ASI:One shared chat showing the complete primary workflow.
- [ ] Accessible **3–5 minute demonstration video**, using [DEMO.md](DEMO.md).
- [ ] Brief problem, target users, and executable outcome description, using [COMPETITION.md](COMPETITION.md).
- [ ] Explain buyer and pricing as hypotheses, using [BUSINESS_MODEL.md](BUSINESS_MODEL.md).
- [ ] Enter every required link through the project-submission workflow and verify accessibility.

The [official hackpack](https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack) is the authority for competition requirements and submission instructions. Record the final submission acknowledgment after the dashboard confirms receipt.
