# Quick demo in ASI:One

Use **one conversation** with [EventRelay Coordinator](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu). Keep EventRelay selected in **To** / retain its `@mention` for every message. This uses the synthetic wedding roster; staff decisions and physical work are simulated.

## First-time test

1. Sign in to ASI:One and open the coordinator link above. Start your own test conversation; the [public shared-chat evidence](https://asi1.ai/shared-chat/69fc8518-55f8-4b17-bd88-59988ba627f7) is for viewing the recorded demonstration.
2. Check **To** above the message box. Select the actual **EventRelay Coordinator** result if it is missing; its handle is `@eventrelay-coordinator` and its address starts with `agent1qw8wdau`. Keep that recipient/mention in subsequent messages.
3. Send `help` once and wait for an actual EventRelay response. Then send `roster` to check current availability.
4. For a read-only example, send `status ER-4DE240CA`. It should show the already-closed synthetic audio demonstration. This does not create a new task.
5. Ask `Show me the current status of all open event issues` for a read-only overview of visible issue references, status and owner. To test the full workflow, choose a service with available crew, then send one report with its location. Keep its returned issue ID and use the same conversation through confirmation. Closure belongs to the original reporter or configured organizer.

**Choose the scenario from the current roster.** The Audio/Stage script below is an example. Later rehearsals and evaluations may occupy either audio crew member or other categories. On 27 October a controlled Power/Entrance test used Pooja and closed as ER-02125351. Its closure released that reservation, but future availability can change. Existing accepted incidents retain their owners until the workflow advances; do not clear or falsely close them to make a test pass.

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

## If the display is slow

- Wait for the **actual EventRelay response and state** before taking the next action. A spinner or your outgoing message alone is not success.
- Use `status ER-XXXXXXXX` to read the current issue. Status is a read; it does not create another incident.
- **Wait before resending the original problem.** Repeating a report as a new message can create another task. Use its issue ID to check status instead.
- Avoid clicking the same work action again while its result is uncertain. Once status is known, continue from the latest card.
- If the room itself cannot load, record that limitation. The organizer-recommended **Agentverse → Agent Profile → Testing → Manual Testing** route is separate evidence; do not label it ASI:One web completion.

A clean Audio/Stage incident completed this primary ASI:One web workflow, including reopening and reporter-confirmed closure, at approximately **18:44 IST**. See [ASI_WEB_PROOF.md](ASI_WEB_PROOF.md) for the actual mixed card/text sequence and observed delays. This guide is an operating script; current staff availability and response latency can differ between rehearsals.
