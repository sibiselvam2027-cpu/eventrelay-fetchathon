# Quick demo in ASI:One

Use **one conversation** with [EventRelay Coordinator](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu). Keep EventRelay selected in **To** / retain its `@mention` for every message. This uses the synthetic wedding roster; staff decisions and physical work are simulated.

## First-time test

1. Sign in to ASI:One and open the coordinator link above. Start your own test conversation; the [public shared-chat evidence](https://asi1.ai/shared-chat/69fc8518-55f8-4b17-bd88-59988ba627f7) is for viewing the recorded demonstration.
2. Check **To** above the message box. Select the actual **EventRelay Coordinator** result if it is missing; its handle is `@eventrelay-coordinator` and its address starts with `agent1qw8wdau`. Keep that recipient/mention in subsequent messages.
3. Send `help` once and wait for an actual EventRelay response. Then send `roster` to check current availability.
4. For a read-only example, send `status ER-4DE240CA`. It should show the already-closed synthetic audio demonstration. This does not create a new task.
5. Ask `Show me the current status of all open event issues` for a read-only overview of visible issue references, status and owner. To test the full workflow, choose a service with available crew, then send one report with its location. Keep its returned issue ID and use the same conversation through confirmation. Closure belongs to the original reporter or configured organizer.

**Choose the scenario from the current roster.** The Audio/Stage script below is an example. Later rehearsals and evaluations may occupy either audio crew member or other categories. On 27 October a controlled Power/Entrance test used Pooja and closed as ER-02125351. A later guarded workflow, **ER-A8B0154D**, also used actual Facilities-agent acceptance for synthetic Pooja and reached original-reporter-confirmed closure at **10:21 IST**; a fresh status read at **10:22 IST** still showed closed. Availability can change after either observation. Existing accepted incidents retain their owners until the workflow advances; do not clear or falsely close them to make a test pass.

A fresh ASI:One `help` test passed at **19:59 IST**. A subsequent read-only ASI:One roster check at **20:00 IST on 24 October** confirmed **Ravi available**, Sara busy, and water backup Neha busy. Cleanup and power crews were available. This is a point-in-time check: send `roster` with the coordinator still selected before a fresh rehearsal and use the actual returned availability.

## Report once, then follow the same issue

| Step | Say or click | Wait until you see |
|---|---|---|
| 1 | **“The microphone has stopped working at the Stage. Please send the audio team.”** Send this once. | A new issue ID, Audio, and Stage. If a guided form appears, choose those fields and submit it. |
| 2 | **Refresh status**, or `status ER-XXXXXXXX` using the returned ID. | A named **accepted owner**. An offer or message-delivery acknowledgment is not acceptance. Demo vendor agents supply their configured decisions automatically. |
| 3 | On the **latest card**, click **Demo: Start work**. Text alternative: `start ER-XXXXXXXX`. | **In progress**. Say that you are simulating the crew's physical action. |
| 4 | Click **Demo: Report completed**. Text alternative: `done ER-XXXXXXXX: The microphone was repaired and tested in this simulation.` | **Awaiting confirmation**. The issue must remain open until the reporter responds. |
| 5 | Click **Still a problem**. Text alternative: `reopen ER-XXXXXXXX: The microphone is still cutting out in this simulation.` | The **same issue ID** reopens and reaches another explicit acceptance. |
| 6 | Use the newest **Demo: Start work**, then wait. Use the newest **Demo: Report completed**, then wait. | In progress, then awaiting confirmation again. |
| 7 | As the **original reporter in this same conversation**, click **Yes, resolved**. Text alternative: `confirm ER-XXXXXXXX`. | **Closed**, with the same incident ID and retained activity history. |

Replace `ER-XXXXXXXX` with your actual issue ID. Button labels come from the current issue card; do not act from an older card after the issue changes.

## Phase-two review requests

The final combined source suite passes **144 tests**, and all five hosted builds compile. All five final seven-module deployments matched saved-source readback and restarted successfully. A native review request on **ER-A8B0154D** preserved Pooja's accepted ownership, operational status and offer version before work continued. The final coordinator evaluation scored **80% (4/5)**; Hospitality **40%**, Audio **40%**, Facilities **60%** and Housekeeping **40%**. These percentages are evaluation results, not profile ratings or a guarantee that every request can be fulfilled. See [the full evidence and remaining failures](RATING_IMPROVEMENTS.md).

Use the coordinator in the same original conversation. Do not substitute an invented issue reference:

| Intent | Say | Expected behavior |
|---|---|---|
| Learn the process | `How do I escalate an issue?` | Instructions and visible issue choices only. No request or incident change. |
| Request review of your unresolved issue | `Please escalate ER-XXXXXXXX` with your actual reference. | The original reporter or configured organizer can record review. Ownership, work status, offer version and deadlines remain intact. No crew is reassigned and no human notification is claimed. |
| Request review without knowing an issue ID | `The crew has not responded. Can you escalate it?` | A real unlinked `RV-XXXXXXXX` request is saved as queued for this conversation. No incident is guessed or changed. Keep the RV reference and provide the missing problem/location or actual issue reference for organizer context. |
| Inspect your requests | `my review requests` | Your conversation's queued requests only. This is read-only. |
| Inspect the aggregate queue | `organizer review queue` | Available only to the configured organizer identity, even in demo mode. An ordinary chat must be denied. |

A message-delivery retry uses the same request ID; sending a new message can create another review item. The queue is limited to 20 items per conversation. A review request is not a new service incident, a verified fix or a completed organizer action. It does not close an incident. An issue awaiting confirmation still needs **Yes, resolved** or **Still a problem** from its authorized reporter.

## Phase-two public specialist guides

Open a specialist and ask a scope or routing question. These deployed FAQs provide question-specific instructions and do not need ASI1 reasoning:

| Specialist | Example public question |
|---|---|
| [Hospitality](https://asi1.ai/ai/agent1qfrq6l9ta28f4xwn5twktttqns0fczgu3ueghkksrl900j6yl4v6ukxs3ng) | “Where should I report that drinking water has run out in the Dining Hall?” |
| [Audio](https://asi1.ai/ai/agent1qga2l6uypaq0ks2sjl4e2jak650naa0dljznq5kxg34jfs2fsvjnq4da69d) | “What microphone and speaker issues do you coordinate?” |
| [Facilities](https://asi1.ai/ai/agent1qvxj23fgwdjncysveppxwmzx8yhx5rf9a6ssclxzk56ftj9gyfsgvxh8xkx) | “Where should I report that the lights have gone out at the Entrance?” |
| [Housekeeping](https://asi1.ai/ai/agent1qgm0yx34j7qjcqnhjdpvftlwv295cdd0hlysrkqc0tp4zwxn70s0scfct3w) | “Where should I report a spill near the Washrooms?” |

Expect the specialist's own category and the **EventRelay Coordinator link**, with instructions for the question you asked. A new report must be copied into the coordinator chat yourself; the specialist has not forwarded it, created a job or contacted crew. For an existing issue, use its actual reference in your authorized coordinator conversation rather than creating another report. A public specialist cannot verify physical work or confirm closure for the original reporter. Public help exposes no private issue or crew records. An ordinary visitor's `accept`, `decline`, `start` or `done` command must still be rejected as unauthenticated. Genuine crew actions require a trusted sender mapping and a matching coordinator offer.

## Check that the recorded state holds

Run one controlled rehearsal at a time and wait for each actual reply. After **Yes, resolved**, send `status ER-XXXXXXXX` with the same actual reference and verify **closed**. The older recorded audio example, `status ER-4DE240CA`, remains a useful check of retained history. A rating or a completed evaluation does not replace this workflow check.

A stale-snapshot rollback was caught during the update and reproduced in a regression test. The deployed guard skips unchanged domain and transport writes, checks the visible stored baseline before a changed checkpoint, and saves state before sending crew operations. It retains a **single coordinator writer** assumption and depends on storage reads exposing current values; it is not a distributed compare-and-swap guarantee. If EventRelay says an update could not be saved safely, refresh status and act only from the latest card. No new crew operation is sent by that rejected request.

The guarded **ER-A8B0154D** workflow reached closed at **10:21 IST on 27 October 2026** and remained closed on a fresh read at **10:22 IST**. After a controlled coordinator **Stop / Start**, without source edits or a state reset, a new reply at **10:23 IST** still showed **closed**, **Pooja** and retained activity history. The older **ER-4DE240CA** audio incident also remained closed with Ravi. This is observed persistence across that specific restart, subject to the storage limitations above.

## If the display is slow

- Wait for the **actual EventRelay response and state** before taking the next action. A spinner or your outgoing message alone is not success.
- Use `status ER-XXXXXXXX` to read the current issue. Status is a read; it does not create another incident.
- **Wait before resending the original problem.** Repeating a report as a new message can create another task. Use its issue ID to check status instead.
- Avoid clicking the same work action again while its result is uncertain. Once status is known, continue from the latest card.
- If the room itself cannot load, record that limitation. The organizer-recommended **Agentverse → Agent Profile → Testing → Manual Testing** route is separate evidence; do not label it ASI:One web completion.

A clean Audio/Stage incident completed this primary ASI:One web workflow, including reopening and reporter-confirmed closure, at approximately **18:44 IST**. See [ASI_WEB_PROOF.md](ASI_WEB_PROOF.md) for the actual mixed card/text sequence and observed delays. This guide is an operating script; current staff availability and response latency can differ between rehearsals.
