# EventRelay live Agentverse deployment

Verified on **24 October 2026 at approximately 15:38 IST (10:08 UTC)** using `avctl hosting logs` against each deployed address. These are Agentverse-hosted deployments. They do not depend on a running local mailbox agent or a custom frontend.

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

Open the Coordinator profile above and use **Chat with Agent** to enter the ASI:One conversation. The intended user interface is ASI:One, including native clarification, progress, and confirmation cards.

Cloud startup and registration are verified here. A successful ASI:One workflow, public shared-chat URL, logged-out profile access, and demo video must be verified and recorded separately. This document does not treat registration alone as proof of ASI discovery or completed workflow execution. No unverified ASI deep link has been invented.

The supplied event, crew identities, staff decisions, and physical work remain explicitly labelled demonstration data. Hosted agent execution and inter-agent messages are separate from any claim that real event staff were contacted or physical work occurred.
