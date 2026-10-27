# EventRelay Hospitality: Drinking-Water Crew Coordination

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

EventRelay Hospitality handles **drinking-water refill offers and authorized crew responses** within EventRelay's synthetic wedding demonstration. It is one of five separate Agentverse Hosted Agents using direct uAgents and Agent Chat Protocol (ACP).

Public chat provides static category, location and reporting guidance with the coordinator link. It does not create an issue or forward a report. Crew actions remain private and authenticated.

## Where to report a problem

Start with [EventRelay Coordinator in ASI:One](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu), for example:

> Drinking water has run out in the Dining Hall. Please coordinate a refill crew.

The coordinator clarifies the category and location, creates an issue reference and sends an offer to this specialist when appropriate. Supported event locations are Stage, Dining Hall, Entrance and Washrooms. **A water spill belongs to Housekeeping; a leaking pipe needs organizer review.** This endpoint does not book catering, order supplies or repair plumbing.

## What this specialist executes

- Receives typed drinking-water offers only from the configured coordinator, for its allowed hospitality crew subset.
- Preserves the issue reference, staff target and offer version in its inbox.
- Relays authenticated crew acceptance/decline or versioned start/completion evidence to the coordinator for validation.
- In the configured demonstration, returns a labelled primary decline or backup acceptance when eligible staff are offered the job. Availability is persistent; acceptance is not guaranteed.

Public chat does not establish a crew identity or accept work. Staff commands require an existing trusted sender mapping and a matching received offer. Progress requires the current issue version. A forwarded reply means it was sent for validation, not that the issue changed successfully.

Physical refilling is simulated. This agent never confirms a repair or closes an issue: the original reporter in the original coordinator conversation, or a configured organizer, confirms resolution. No WhatsApp, voice, payments or real staff signup is implemented.

[Source and testing guide](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon)
