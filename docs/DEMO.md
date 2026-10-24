# EventRelay — four-minute demonstration

## Preparation

- Deploy and verify all five agents as **Agentverse Hosted Agents** before recording. Hosted code, persistence, deployment, and discoverability are pending until that verification is complete.
- Use the synthetic wedding roster. Begin with no open drinking-water incident.
- Keep every user-facing step in ASI:One. Use supported native staff cards or an authenticated staff conversation to perform crew actions. Do not substitute a custom webpage or local console for the judged workflow.
- The five agents are the coordinator plus hospitality, audio, facilities, and housekeeping. For the main story, the coordinator exchanges offers and responses with the hospitality agent; the other agents remain available for their own categories.
- Label the screen or introduction: **“Demonstration event and staff; physical work is simulated.”**
- If a feature in this script is unavailable in the tested build, remove that claim or use the shorter verified path. Do not narrate a successful operation that the software did not perform.
- Confirm that an issue and its history survive separate hosted invocations. A direct uAgents/ACP implementation does not alone demonstrate successful deployment or discovery.

## Main story

| Time | Presenter action and words | Evidence to show |
|---|---|---|
| 0:00–0:25 | “At a wedding, the caterer, sound team, venue staff, and family all work together, but they have different responsibilities. When a problem happens, one coordinator has to find someone, chase them, and update the family. EventRelay keeps that handoff accountable.” | ASI:One coordinator; demonstration-data label |
| 0:25–0:45 | Report: **“There is a water issue in the Dining Hall.”** | A short clarifying question rather than a guessed assignment |
| 0:45–1:05 | Clarify: **“The drinking water has run out. Guests are waiting.”** | Recorded category and location; issue ID; an offer to Arun |
| 1:05–1:25 | “The task is offered, but nobody owns it yet.” As Arun, decline through the supported staff action: **“I cannot take this; I am handling the buffet.”** | Explicit decline; task offered to Neha; original issue ID retained |
| 1:25–1:45 | As Neha, accept, then mark work in progress. “Now we have an accountable owner. The coordinator did not mistake a delivered message for acceptance.” | Neha as accepted owner; state transition and timestamp |
| 1:45–2:05 | As Neha, report completion: **“Drinking-water dispensers refilled.”** | **Awaiting confirmation**, not Closed |
| 2:05–2:30 | As the reporter, respond: **“Not fully resolved. The second counter still has no water.”** | Same incident reopened, new details preserved, another offer or reassignment |
| 2:30–3:00 | Complete the supported acceptance/work/completion steps. As the reporter, confirm: **“Both counters now have drinking water. Resolved.”** | Closed only after reporter confirmation |
| 3:00–3:25 | “Here is the history: report, clarification, decline, backup acceptance, work, disputed completion, and confirmed resolution.” | Persistent activity history; responsible people and timestamps |
| 3:25–3:50 | Run one pretested exception: an offer expires and reaches its approved backup, **or** all eligible staff decline and the issue escalates to the organizer. | An actual recorded timeout/reassignment or visible unresolved escalation |
| 3:50–4:00 | “EventRelay turns a complaint into an accountable handoff and a confirmed outcome. Our next test is with an event planner using their own roster and escalation rules.” | Final status; no invented customer or business metrics |

If using a shortened timer to show escalation, say **“The demo timer is accelerated.”** An estimated arrival time must come from a crew response or an explicitly labelled test policy.

## Optional cross-team demonstration

Use this instead of the main story only when dependency handling has passed testing:

1. Report an audio fault at the Stage.
2. The AV worker accepts and reports that facilities assistance is required.
3. Create a linked power/facilities task. Keep the original audio task open and blocked.
4. The authorized facilities worker completes the relevant work and the appropriate reporter confirms it.
5. AV resumes, tests the microphone, and reports completion.
6. The original reporter confirms whether the sound issue is resolved.

Describe these as staff-reported actions. The agent must not diagnose a fault or declare the area safe on its own.

## Judge questions — short answers

**Why not use a WhatsApp group?**

“A group helps people communicate. Our workflow records who accepted responsibility, what remains overdue, why a handoff failed, and whether the reporter confirmed the result. The demonstration shows those state changes, not just messages.”

**Why separate agents?**

“One hosted coordinator works with four hosted vendor agents: hospitality, audio, facilities, and housekeeping. Each vendor team owns different staff and acceptance rules. Direct uAgent messages carry requests and decisions; ACP keeps the user workflow in ASI:One. That separation mirrors the independent organizations at an event.”

**What if nobody accepts?**

“The issue stays unresolved and visibly escalates to the designated organizer. The system cannot manufacture staff or claim that the problem is fixed.”

**How do you know the work was done?**

“Crew completion and reporter confirmation are separate records. The POC records their statements. It does not claim independent sensor verification of a physical repair.”

**Can a guest close someone else's job?**

“The intended control is that only the original reporter or designated organizer can confirm closure, and only eligible assigned staff can act on the job. We demonstrate the implemented authorization checks.”

**Does this already exist?**

“Incident and wedding-management systems exist. Our proposed focus is a conversational event-day workflow across temporary vendor teams, with explicit acceptance and recovery when a handoff fails.”

**Who pays?**

“The proposed buyer is a planner or venue operator. We would begin with a per-event pilot, then test a subscription for repeat-event teams. The family and crew are users. Pricing and willingness to pay are hypotheses; we have not claimed paying customers.”
