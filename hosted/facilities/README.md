# EventRelay Facilities: Power and Lighting Crew Coordination

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

EventRelay Facilities handles **power/lighting crew offers and authorized staff responses** in EventRelay's synthetic wedding demonstration. It runs as a separate Agentverse Hosted Agent using direct uAgents and Agent Chat Protocol (ACP), alongside the coordinator and three other specialists.

Public chat offers static scope, location and coordinator-handoff guidance. It does not send a report, assign staff or issue a safety judgment. Worker actions remain authenticated.

## Where to report a problem

Send the problem to [EventRelay Coordinator in ASI:One](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu), for example:

> The lights have gone out at the Entrance. Please coordinate the facilities crew.

The coordinator clarifies the report, assigns an issue reference and selects eligible staff before sending a power offer here. Supported event locations are Stage, Dining Hall, Entrance and Washrooms. A silent microphone, water refill or cleanup request belongs to the relevant other specialist through the coordinator.

## What this specialist executes

- Receives matching power offers only from the configured coordinator and only for its allowed facilities staff subset.
- Retains the issue reference, staff target and offer version.
- Relays authenticated acceptance/decline and versioned start/completion evidence for coordinator validation.
- In the configured demo, returns a labelled simulated acceptance for eligible configured crew offers. Persistent roster capacity can prevent assignment.

Public messages cannot accept a facilities job or impersonate crew. Staff commands require an existing trusted sender mapping and a matching received offer. Progress requires the current issue version. A transport acknowledgment or forwarded response does not prove that a worker accepted, arrived or restored power.

This is a coordination prototype, not electrical diagnosis, emergency dispatch or safety certification. It does not repair a leak or operate equipment. Physical work is simulated. Only the original reporter in the original coordinator conversation, or a configured organizer, can confirm resolution; this specialist never closes an issue. No WhatsApp, voice, payments or real staff signup is implemented.

[Source and testing guide](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon)
