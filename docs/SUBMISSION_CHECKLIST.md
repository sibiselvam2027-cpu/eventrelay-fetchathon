# EventRelay — submission checklist

**Updated deadline: 11:59 PM IST, 24 October 2026, according to the organizer announcement shared with the team.** That announcement reports ASI:One downtime and recommends **Agent Profile → Testing → Manual Testing** in Agentverse. This is a supplied organizer statement, not an independently measured platform-wide availability claim. Earlier 16:45/17:00 internal targets are superseded. Keep the original public hackpack requirements visible and distinguish the recommended alternative from completed ASI:One UI evidence.

## Verified code evidence

- [x] Public repository: [sibiselvam2027-cpu/eventrelay-fetchathon](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon).
- [x] CI-verified current source: `3e96df2b4dde0fbede5e671ef53d6a2b1410c2b2`.
- [x] Initial local verification: **65 tests passed** before publication.
- [x] Published source fixes: **68 tests passed locally and in CI**.
- [x] SDK-client/guided-recovery source: **69 local and CI tests passed**; all five hosted projects rebuilt and compiled.
- [x] Additional timeout-recovery regression: **70 tests passed in CI**. [Verify EventRelay](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40086612325)
- [x] CI job logs confirm the 70-test baseline; hosted-project build/compile and synthetic-workflow checks also passed. [CI job](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40086612325/job/120850745755)
- [x] CRLF normalization and stored-route migration source: **73 local and CI tests — OK**. [Verified CI](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40087069509)
- [x] Final envelope-lifetime and safe-diagnostic revision: **74 local and CI tests — OK**; five hosted builds/compilation and the synthetic scenario passed. [Final source CI](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40089811983)
- [x] Own-routing-mention/native-JSON and colon-command regressions: **81 local and CI tests — OK**; five hosted builds/compilation and the synthetic scenario passed. [Current source CI](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40095406290)
- [x] Longer bounded ASI request and safe timeout/connection/HTTP diagnostics: **83 local and CI tests — OK**; hosted build/compile and the synthetic scenario passed. [Latest source CI](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon/actions/runs/40095925245)
- [x] Deployed 83-test revision: live ASI1 extraction of “show status of ER-A50BFBB4” returned the actual closed issue/Neha/native card through Agentverse Manual Testing at approximately 18:28 IST. This is API-path evidence, not complete ASI:One web evidence.

The configuration/migration changes have passed CI. Local or CI success does not complete the live ASI:One UI evidence items below.

## Live hosted deployment

All five roles must run as Agentverse Hosted Agents. ASI:One is the intended product interface. The implementation uses direct uAgents/ACP and typed messages, with persistent Agent Storage. Agentverse Manual Testing is the organizer-recommended demonstration/testing route during the reported disruption.

| Hosted agent | Actual agent address | Public profile URL | Running and verified |
|---|---|---|---|
| Coordinator | `agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu` | Public access pending | Hosted lifecycle across four service categories verified |
| Hospitality | `agent1qfrq6l9ta28f4xwn5twktttqns0fczgu3ueghkksrl900j6yl4v6ukxs3ng` | Public access pending | Decline, backup acceptance and water closure verified |
| Audio | `agent1qga2l6uypaq0ks2sjl4e2jak650naa0dljznq5kxg34jfs2fsvjnq4da69d` | Public access pending | Audio closure and same-ID reopening verified |
| Facilities | `agent1qvxj23fgwdjncysveppxwmzx8yhx5rf9a6ssclxzk56ftj9gyfsgvxh8xkx` | Public access pending | Power incident acceptance and closure verified |
| Housekeeping | `agent1qgm0yx34j7qjcqnhjdpvftlwv295cdd0hlysrkqc0tp4zwxn70s0scfct3w` | Public access pending | Cleanup incident acceptance and closure verified |

- [x] Five hosted identities created and their public addresses recorded.

- [x] Deploy and start all five hosted agents; retrieved cloud logs show successful starts and registration. See [LIVE_DEPLOYMENT.md](LIVE_DEPLOYMENT.md).
- [x] Configure actual cross-agent addresses and verify message exchanges across all four service categories.
- [x] Verify one live natural-language status lookup without exposing credentials. Complete natural-language report/clarification testing remains pending.
- [x] Verify persistent issues, offers, and reporter routes across hosted invocations and same-ID reopening.
- [ ] Complete agent profiles and README information; verify ACP interaction and ASI:One discovery rather than assuming either from successful upload.

- [x] ASI:One reached the deployed coordinator and displayed an actual agent reply at approximately 15:40 IST. [Observed direct entry](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu)

That earlier reply reported ASI1 authentication failure. Later hosted status lookups and a clean primary Audio/Stage ASI:One web workflow succeeded. Frontend delays and some loading failures were observed; the verified clean flow and remaining public shared-chat requirement are recorded below. Further language/clarification cases are not inferred from one completed report.

The latest source offers an explicitly labelled manual guided form inside ASI:One when ASI1 is unavailable. It creates no issue or offer until the user submits the required details. A fresh web attempt rendered and submitted that form, created ER-11B37F67, and reached Neha's acceptance. This fallback is not evidence that natural-language understanding works or that the later web workflow completed.

Earlier temporary observer tests confirmed report dispatch but received no callbacks before stopping; those tests alone establish no acceptance or closure. Later hosted rehearsals supplied the positive four-category evidence below. Diagnostic agents are not submitted product roles.

## ASI:One primary workflow — verified; shared chat pending

**Clean primary web result:** ER-4DE240CA correctly interpreted a new microphone report as Audio/Stage, reached actual vendor-agent Ravi acceptance, progressed through work/completion, reopened under the same ID, reaccepted, and closed after the original reporter's native confirmation around **18:44 IST**. [Sanitized proof](ASI_WEB_PROOF.md); a closure screenshot is retained locally. The run used native cards and text commands with rendering delays and one stale-action warning. [Use the Audio/Stage quick start](QUICK_DEMO.md); the interrupted water issue remains open and consumes hospitality capacity.

**Separate verified results:** hosted water, audio, power, and cleanup incidents reached closure by 16:25:07 IST. Water used primary decline/backup acceptance; audio reopened and reaccepted under the same ID. One natural-language status lookup succeeded. Vendor decisions and physical/reporter actions were explicitly synthetic. [Evidence](LIVE_WORKFLOW_PROOF.md). The ASI:One UI checklist below remains pending because these rehearsals did not use the complete frontend workflow.

- [ ] Report an ambiguous water issue; clarify it before dispatch.
- [ ] Show that an offered task has no accepted owner yet.
- [ ] Record a primary worker's decline and a backup's explicit acceptance.
- [x] Interpret a clean new natural-language Audio/Stage report through live ASI1 and record the actual vendor agent's acceptance.
- [x] Show progress, worker-reported completion, and awaiting confirmation through ASI:One web.
- [x] Reject an incomplete fix, reopen the same issue, reaccept, and confirm the eventual resolution through ASI:One web.
- [ ] Demonstrate a real timeout/escalation or a cross-team dependency that passed testing.
- [x] Observe a stale-action warning when an old Done action was repeated during web-rendering uncertainty.
- [ ] Demonstrate live role-restriction negative cases separately from the passing source tests.
- [ ] Create and open the **public ASI:One shared-chat URL**: Pending.

Keep demonstration people, configured responses, accelerated timers, and simulated physical work clearly labelled. A local test, protocol acknowledgment, or crew completion report is not proof of a real-world repair.

## Organizer-recommended Manual Testing demonstration

- [x] Record the supplied organizer announcement's deadline extension and recommended testing route without publishing its screenshot or private contact details.
- [x] Open the hosted coordinator's Agentverse profile, then **Testing → Manual Testing**.
- [x] Complete the exposed chat protocol and native form/card callbacks through guided category/location entry, actual vendor decline/backup acceptance, progress, awaiting confirmation, same-ID reopening, and reporter-confirmed closure. Incident **ER-3CC6223A**, completed **17:55:05 IST**. [Sanitized proof](MANUAL_TESTING_PROOF.md)
- [x] Keep the same issue and reporter session throughout; staff decisions and physical work are synthetic. The presenter never clicked Accept; the actual hospitality agent supplied its configured decisions.
- [x] Prepare a **4:27.17 narrated edited walkthrough** of actual Manual Testing screenshots: local deliverable `EventRelay-demo.mp4`, with script `EventRelay-narration.txt`. Audio/video decoding and the visual contact sheet were checked. This is **not a continuous live recording**; the demonstrated callbacks are genuine and physical work is synthetic.
- [ ] Upload the finished local video and verify a publicly accessible video URL.
- [x] Label this earlier rehearsal **Agentverse Manual Testing**. A later primary ASI:One web workflow completed separately; public shared-chat access remains pending.
- [ ] Follow any further organizer submission instructions and retain the final receipt. A recommendation to use Manual Testing does not by itself prove that every original deliverable was waived.

## Submission packet — pending

- [ ] Public repository URL and instructions to run/test the project.
- [ ] Five actual Agentverse profile URLs and agent addresses.
- [ ] Public ASI:One shared chat showing the complete primary workflow.
- [ ] Publicly accessible **3–5 minute demonstration video** — local 4:27.17 video is ready; public URL pending.
- [ ] Brief problem, target users, and executable outcome description, using [COMPETITION.md](COMPETITION.md).
- [ ] Explain buyer and pricing as hypotheses, using [BUSINESS_MODEL.md](BUSINESS_MODEL.md).
- [ ] Enter every required link through the project-submission workflow and verify accessibility.

The [official hackpack](https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack) is the authority for competition requirements and submission instructions. Record the final submission acknowledgment after the dashboard confirms receipt.
