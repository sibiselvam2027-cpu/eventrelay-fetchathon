# EventRelay Audio: Microphone and Speaker Crew Coordination

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

EventRelay Audio receives **audio issue offers and authorized AV crew responses** for EventRelay's synthetic wedding demonstration. It is a separate Agentverse Hosted Agent, connected to the coordinator through direct uAgents, Agent Chat Protocol (ACP) and typed offer/decision messages.

Public chat explains the audio category, supported locations and how to report through the coordinator. It never forwards a public report or assigns crew. Staff actions require authentication.

## Where to report a problem

Use [EventRelay Coordinator in ASI:One](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu), for example:

> The microphone has stopped working at the Stage. Please send the audio team.

The coordinator records and clarifies the report, selects eligible roster staff and sends the matching audio offer here. Event locations are Stage, Dining Hall, Entrance and Washrooms. Requests for drinking water, electrical work or cleanup go through the coordinator to the appropriate other specialist.

## What this specialist executes

- Receives typed audio offers only from the configured coordinator and only for its allowed AV staff subset.
- Stores the received issue reference, target staff and offer version.
- Forwards authenticated crew acceptance/decline and versioned progress evidence for coordinator validation.
- Under the configured demo policy, returns a labelled simulated acceptance for eligible configured crew offers. Busy or unavailable staff are not a promise of acceptance.

An ordinary visitor cannot become AV staff by claiming a name or sending `accept`. Staff commands require an existing trusted sender mapping and a matching received offer. Start/completion evidence requires the current issue version. Forwarding a reply does not establish successful completion.

This agent coordinates handoffs; people perform the physical work. It does not diagnose or repair hardware, stream music or certify sound quality. Physical work is simulated, and the specialist cannot confirm or close an issue. The original reporter must confirm in the original coordinator conversation, or a configured organizer may confirm. No WhatsApp, voice, payments or real staff signup is implemented.

[Source and testing guide](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon)
