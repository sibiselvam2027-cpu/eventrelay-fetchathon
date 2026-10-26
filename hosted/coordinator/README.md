# EventRelay Coordinator: Event Issue Dispatch and Follow-up

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

EventRelay helps event planners, venue coordinators and event participants report a service problem, find an accountable crew member and verify the outcome. In ASI:One, describe the problem and location. The coordinator clarifies missing details, selects eligible roster staff, records explicit acceptance, follows up and keeps the issue open until the original reporter or configured organizer confirms resolution.

## Supported services and locations

This prototype uses one **synthetic wedding event** with four service categories:

| Category | Responsible agent | Example report |
|---|---|---|
| Audio | EventRelay Audio | “The microphone has stopped working at the Stage. Please send the audio team.” |
| Drinking water | EventRelay Hospitality | “Drinking water has run out in the Dining Hall.” |
| Power / facilities | EventRelay Facilities | “The lights have gone out at the Entrance.” |
| Cleanup | EventRelay Housekeeping | “There is a spill near the Washrooms.” |

Supported locations are **Stage, Dining Hall, Entrance and Washrooms**. Priority can be normal or urgent. An ambiguous “water issue” needs clarification before routing.

## How to use

1. [Open EventRelay in ASI:One](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu). Keep the coordinator selected as the recipient for every message.
2. Send `help`, then `roster` to check current demo crew availability. Report one problem with its location and answer any clarification form.
3. Keep the returned `ER-XXXXXXXX` issue reference. Use **Refresh status** or `status ER-XXXXXXXX` instead of repeatedly submitting the original report.
4. Wait for a named accepted owner. Follow the latest **Demo: Start work** and **Demo: Report completed** cards to simulate crew progress.
5. In the **same original conversation/session**, choose **Yes, resolved** to close, or **Still a problem** to reopen the same issue ID. A different chat is not the original reporter identity.

Example output excerpt, with a placeholder reference:

```text
DEMO: synthetic wedding, people, and physical work.
ER-XXXXXXXX · Audio · Stage
The microphone has stopped working at the Stage.
Status: offered
Accountable owner: Nobody has accepted yet
Offer sent to Ravi; acceptance is still pending.
```

After the vendor accepts, status becomes `accepted` with the owner's name. Crew completion produces `awaiting confirmation`, not closure. Declines or expired offers try an eligible backup. Unavailable capacity and overdue follow-up remain visibly escalated. Issue state and activity history persist in Agentverse storage.

## Five-agent coordination

The coordinator and four category agents are separate **Agentverse Hosted Agents**, using direct **uAgents**, **Agent Chat Protocol (ACP)** and typed offer/decision messages. ASI1 interprets natural-language intent; code validates actions and permissions. ASI:One text, forms and cards provide the interface. Message delivery alone never counts as crew acceptance.

## Demo limits and permissions

Demo vendor agents automatically return configured, labelled decisions: Arun declines and Neha accepts water offers; other configured crew accept when eligible. Demo users can inspect synthetic issues and simulate staff progress. Physical work is simulated. Real staff access requires trusted sender mappings; claiming a staff name in text grants no authority. Reporter confirmation remains restricted to the original reporter or configured organizer.

Ask `Show me the current status of all open event issues` for an overview of up to 20 open issues visible to your identity, with real references, category, location, status and owner. Demo issues are synthetic and visible to demo users. Outside demo mode, the overview follows the existing reporter, assigned-crew and organizer permissions. The overview does not create issues, dispatch crew or change progress. For overdue work, select an actual reference and check its status and recorded escalation.

Use the newest card after state changes. ASI:One responses can be delayed. If ASI1 fails, a labelled manual form requests category/location before dispatch. This is not emergency response, hazard diagnosis, real crew signup, multi-event management, WhatsApp, voice, payments or a guarantee of repair.

[Public source and testing guide](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon) · [Recorded public demonstration](https://asi1.ai/shared-chat/69fc8518-55f8-4b17-bd88-59988ba627f7)
