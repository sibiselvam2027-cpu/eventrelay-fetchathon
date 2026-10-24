# EventRelay — submission checklist

**Working target: 16:00 IST, 24 October 2026, as requested.** This checklist separates verified code evidence from live deployment and submission evidence. Update it only when each check has actually succeeded.

## Verified code evidence

- [x] Public repository: [sibiselvam2027-cpu/eventrelay-fetchathon](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon).
- [x] Published commit verified: `6a67685ed784b8dfa88aa67da31facddeb13c133`.
- [x] Initial local verification: **65 tests passed** before publication.
- [x] Current source fixes: **68 tests passed locally**. The updated commit needs its own CI result.
- [x] GitHub Actions passed for that exact commit: [Verify EventRelay, run 1](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40083719828).
- [x] CI job logs independently confirm **65 tests — OK**. The job also passed hosted-project build/compile and the complete synthetic-workflow checks. [CI job](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40083719828/job/120842284947)

The CI run completed at **15:23:31 IST on 24 October 2026**. A later source commit requires its own CI result; the result above does not verify later changes.

## Live hosted deployment — pending until verified

All five roles must run as Agentverse Hosted Agents. ASI:One is the sole product interface. The implementation uses direct uAgents/ACP and typed messages, with persistent Agent Storage.

| Hosted agent | Actual agent address | Public profile URL | Running and verified |
|---|---|---|---|
| Coordinator | `agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu` | Pending verification | Startup, Almanac registration, and interval logs observed; full flow pending |
| Hospitality | `agent1qfrq6l9ta28f4xwn5twktttqns0fczgu3ueghkksrl900j6yl4v6ukxs3ng` | Pending verification | Identity created; full flow pending |
| Audio | `agent1qga2l6uypaq0ks2sjl4e2jak650naa0dljznq5kxg34jfs2fsvjnq4da69d` | Pending verification | Identity created; full flow pending |
| Facilities | `agent1qvxj23fgwdjncysveppxwmzx8yhx5rf9a6ssclxzk56ftj9gyfsgvxh8xkx` | Pending verification | Identity created; full flow pending |
| Housekeeping | `agent1qgm0yx34j7qjcqnhjdpvftlwv295cdd0hlysrkqc0tp4zwxn70s0scfct3w` | Pending verification | Identity created; full flow pending |

- [x] Five hosted identities created and their public addresses recorded.

- [ ] Deploy and start all five hosted agents; inspect their execution logs.
- [ ] Configure their actual cross-agent addresses and verify message exchanges.
- [ ] Configure ASI1 credentials in Agent Secrets; verify natural-language understanding without exposing the key.
- [ ] Verify issue, offer, conversation, and audit state across separate hosted invocations.
- [ ] Complete agent profiles and README information; verify ACP interaction and ASI:One discovery rather than assuming either from successful upload.

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
