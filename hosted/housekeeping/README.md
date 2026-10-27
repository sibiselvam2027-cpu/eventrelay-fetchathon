# EventRelay Housekeeping: Spill and Cleanup Crew Coordination

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

EventRelay Housekeeping handles **spill/cleanup offers and authorized housekeeping responses** in EventRelay's synthetic wedding demonstration. It is one of five separate Agentverse Hosted Agents, using direct uAgents and Agent Chat Protocol (ACP) for category-specific coordination.

Public chat explains cleanup scope, event locations and how to contact the coordinator. It does not forward a complaint, dispatch cleaners or expose private crew records. Staff actions require authentication.

## Where to report a problem

Report through [EventRelay Coordinator in ASI:One](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu), for example:

> There is a water spill near the Washrooms. Please coordinate a cleanup crew.

The coordinator clarifies the category and location, creates the issue reference and sends an eligible cleanup offer here. Supported event locations are Stage, Dining Hall, Entrance and Washrooms. **Empty drinking-water supplies belong to Hospitality; a leaking pipe needs organizer review.** Power and audio requests go to their respective specialists through the coordinator.

## What this specialist executes

- Receives typed cleanup offers only from the configured coordinator and for its allowed housekeeping staff subset.
- Stores the received issue reference, target staff and offer version.
- Forwards authenticated crew acceptance/decline and versioned work-progress evidence for coordinator validation.
- Under the configured demonstration policy, returns labelled simulated acceptance for eligible configured crew offers. Busy staff may leave an issue awaiting another eligible owner or escalated.

An ordinary visitor cannot accept, start or complete a job as housekeeping staff. Staff commands require an existing trusted sender mapping and a matching received offer. Progress requires the latest issue version. Forwarding a crew reply is not confirmation that cleaning occurred.

Physical cleanup is simulated. This agent does not inspect hazards, certify hygiene, repair plumbing or confirm a fix for the reporter. Closure belongs to the original reporter in the original coordinator conversation, or a configured organizer. No WhatsApp, voice, payments or real staff signup is implemented.

[Source and testing guide](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon)
