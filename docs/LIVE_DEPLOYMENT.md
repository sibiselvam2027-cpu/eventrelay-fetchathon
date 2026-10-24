# EventRelay live Agentverse deployment

**Latest primary UI proof:** the deployed 83-test revision completed a clean Audio/Stage ASI:One web issue, including reopening and reporter-confirmed closure, around **18:44 IST**. [Sanitized sequence and screenshot](ASI_WEB_PROOF.md). Public shared-chat access remains pending. The startup and earlier diagnostic history below retain their original time-scoped observations.

Verified on **24 October 2026 at approximately 15:38 IST (10:08 UTC)** using `avctl hosting logs` against each deployed address. These are Agentverse-hosted deployments. They do not depend on a running local mailbox agent or a custom frontend.

**Later positive rehearsals:** water reached closure at 16:16:19 IST after primary decline and backup acceptance. Audio, power, and cleanup also reached closure by 16:25:07 IST; audio reopened and reaccepted under the same issue ID. Actual hosted vendor agents supplied their configured synthetic acceptance decisions. A plain-language status lookup returned the stored closed water incident. See [the sanitized live workflow proof](LIVE_WORKFLOW_PROOF.md). The full ASI:One UI workflow remains unverified.

## Hosted agents

| Agent | Latest successful start, IST | Agentverse profile |
|---|---|---|
| Coordinator | 15:35:28 | [Open profile](https://agentverse.ai/agents/details/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu/profile) |
| Hospitality | 15:35:26 | [Open profile](https://agentverse.ai/agents/details/agent1qfrq6l9ta28f4xwn5twktttqns0fczgu3ueghkksrl900j6yl4v6ukxs3ng/profile) |
| Audio | 15:35:12 | [Open profile](https://agentverse.ai/agents/details/agent1qga2l6uypaq0ks2sjl4e2jak650naa0dljznq5kxg34jfs2fsvjnq4da69d/profile) |
| Facilities | 15:35:25 | [Open profile](https://agentverse.ai/agents/details/agent1qvxj23fgwdjncysveppxwmzx8yhx5rf9a6ssclxzk56ftj9gyfsgvxh8xkx/profile) |
| Housekeeping | 15:35:31 | [Open profile](https://agentverse.ai/agents/details/agent1qgm0yx34j7qjcqnhjdpvftlwv295cdd0hlysrkqc0tp4zwxn70s0scfct3w/profile) |

Public agent addresses:

```text
coordinator:  agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu
hospitality:  agent1qfrq6l9ta28f4xwn5twktttqns0fczgu3ueghkksrl900j6yl4v6ukxs3ng
audio:        agent1qga2l6uypaq0ks2sjl4e2jak650naa0dljznq5kxg34jfs2fsvjnq4da69d
facilities:   agent1qvxj23fgwdjncysveppxwmzx8yhx5rf9a6ssclxzk56ftj9gyfsgvxh8xkx
housekeeping: agent1qgm0yx34j7qjcqnhjdpvftlwv295cdd0hlysrkqc0tp4zwxn70s0scfct3w
```

## Evidence observed

- Every agent logged `EventRelay attach: 09 attached successfully`, followed by `Successfully started agent` in its latest deployment cycle.
- Every agent logged successful Almanac registration: the coordinator reported fast-track registration; the four service agents also reported successful contract registration.
- The coordinator continued logging successful scheduled interval execution. The latest interval in this capture was **15:37:57 IST**.
- No error lines appeared after the latest successful start in the retrieved logs for any of the five agents. Earlier failed startup attempts precede the verified successful deployments.
- A separate `avctl hosting get agent` read reported the coordinator as compiled and running.

Server log timestamps were treated as UTC and converted to Asia/Kolkata for the table above. Verification is a point-in-time observation, not a guarantee of future uptime.

## ASI:One entry and submission evidence

**[Open EventRelay Coordinator in ASI:One](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu).** This is the entry URL observed during live testing. The intended user interface is ASI:One, including native clarification, progress, and confirmation cards.

At approximately **15:40 IST**, ASI:One reached the deployed coordinator and displayed its actual agent response. That response reported **ASI1 authentication failed**. Subsequent ASI:One frontend 503/504 errors affected websocket/history access and follow-up messages stalled. The later diagnostic rehearsal successfully exercised a natural-language status lookup through the hosted coordinator. That successful lookup is narrower than a complete ASI:One UI workflow or all natural-language intents.

A successful complete ASI:One workflow, public shared-chat URL, logged-out profile access, and demo video must still be verified separately. Registration, startup, and an error reply are distinct from a completed workflow.

The latest source adds manual guided-form recovery inside ASI:One when ASI1 fails. The form requires a user-supplied category and location before dispatch; it does not represent successful LLM reasoning. Its live rendering remains pending; the successful natural-language status lookup does not establish form rendering.

## Diagnostic observer result and cleanup

Three test-report dispatches were confirmed at approximately 15:52:10, 15:53:49, and 15:56:17 IST, but no response callbacks reached the temporary observer before it stopped. Retrieved execution logs showed timeouts. No live worker acceptance, reporter-confirmed closure, or complete ASI:One workflow is claimed from those tests.

The observer and a failed-deployment orphan were then removed after exact-ID verification. At that cleanup check, the account inventory contained the five compiled/running EventRelay product agents. Separate diagnostic control agents are not submitted product roles.

## Subsequent configuration fix and hosted verification

Peer-dispatch logs contained a trailing carriage-return character in configured public addresses. The source now normalizes that formatting and migrates stored peer routes without clearing existing issues. Regressions, including the contaminated-configuration lifecycle, pass as part of the 73-test suite. Subsequent deployed rehearsals verified actual vendor exchanges, callback delivery, persistent closure across all four service categories, same-ID audio reopening, and one natural-language status lookup. The complete ASI:One UI workflow remains a separate verification step. An independent minimal control agent also encountered ASI frontend chat-start failures during diagnosis.

The supplied event, crew identities, staff decisions, and physical work remain explicitly labelled demonstration data. Hosted agent execution and inter-agent messages are separate from any claim that real event staff were contacted or physical work occurred.
