# Quick demo in ASI:One

Use **one conversation** with [EventRelay Coordinator](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu). Keep EventRelay selected in **To** / retain its `@mention` for every message. This uses the synthetic wedding roster; staff decisions and physical work are simulated.

**Current recommended scenario: Audio at Stage.** The previous audio rehearsal ER-4DE240CA closed, releasing its assigned worker. Water incident ER-11B37F67 remains open and its backup worker is occupied. Check current status/roster, then use the audio scenario below or continue an existing issue.

A read-only Agentverse roster check at **18:47 IST on 24 October** confirmed **Ravi available**, Sara busy, and water backup Neha busy. Cleanup and power crews were available. This is a point-in-time check: send `roster` with the coordinator still selected before a fresh rehearsal and use the actual returned availability.

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

## If the display is slow

- Wait for the **actual EventRelay response and state** before taking the next action. A spinner or your outgoing message alone is not success.
- Use `status ER-XXXXXXXX` to read the current issue. Status is a read; it does not create another incident.
- **Wait before resending the original problem.** Repeating a report as a new message can create another task. Use its issue ID to check status instead.
- Avoid clicking the same work action again while its result is uncertain. Once status is known, continue from the latest card.
- If the room itself cannot load, record that limitation. The organizer-recommended **Agentverse → Agent Profile → Testing → Manual Testing** route is separate evidence; do not label it ASI:One web completion.

A clean Audio/Stage incident completed this primary ASI:One web workflow, including reopening and reporter-confirmed closure, at approximately **18:44 IST**. See [ASI_WEB_PROOF.md](ASI_WEB_PROOF.md) for the actual mixed card/text sequence and observed delays. This guide is an operating script; current staff availability and response latency can differ between rehearsals.
