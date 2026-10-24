# EventRelay — business-model review

**Buyer hypothesis: an event-planning agency or venue operator pays for fewer unowned issues and less manual chasing during an event.** The family, designated reporters, coordinators, and crew are users. A wedding family is an occasional user; a planner or venue has the stronger repeat-use opportunity.

This is a proposed business model. No customer interviews, paid pilots, demand figures, savings, or revenue are claimed.

## Initial offer

Start with one paid, assisted event pilot: configure the responsibility roster, staff identities, approved backups, locations, and escalation rules, then observe the event's issue workflow. If repeat-event teams see value, test a monthly subscription with reusable event templates, roster setup, and issue-history reporting. Those recurring features are product hypotheses until built and validated.

Sell a clearly bounded event window and service level. Define how multi-day weddings, concurrent events, onboarding, support hours, record retention, and additional usage are counted before making a commercial offer. An unresolved physical problem is not a software failure automatically; the service must still record it honestly and escalate it.

## Pricing experiments — unvalidated hypotheses

| Candidate offer | Price to test | What must be validated |
|---|---:|---|
| Single-event pilot | ₹999 per event | Whether a planner will pay; the event window, onboarding, and support that can fit economically |
| Agency or venue subscription | ₹3,999 per month, up to five events | Repeat-event frequency, willingness to commit, usage limits, and recurring value beyond individual pilots |

These are unvalidated pricing experiments, not a finalized commercial offer. Test whether repeat-event teams value the subscription and whether its included usage, onboarding, and support are economically viable. Do not advertise measured customer savings before a pilot provides evidence.

Avoid pricing per complaint: it could discourage reporting or make a difficult event unexpectedly expensive. Keep appropriate usage controls, but test an understandable event-based offer first.

## Unit economics to measure

Use the actual model, platform, and support records. Do not insert invented API or hosting rates.

**Variable cost per event = measured LLM input/output usage × effective unit costs + allocated Agentverse hosting/usage charges + support minutes × internal cost per minute.**

**Contribution per event = collected event revenue − variable cost per event.**

Track clarification rounds, unstructured updates, five-agent invocation volume, retries, retained history, and multi-day duration. Deterministic status transitions should not require unnecessary LLM calls. Include onboarding and support time even if founders currently provide it themselves. A subscription's economics depend on both events used and cost per event; unused allowances are not evidence of successful adoption.

Current architecture: five Agentverse Hosted Agents; ASI:One is the sole user interface. Credentials belong in hosted secrets, and persistent workflow state belongs in hosted storage. Hosted implementation, test, deployment, and discoverability status must be verified separately before a customer-facing pilot is promised.

## Main commercial risks

| Risk | Practical implication | Test or response |
|---|---|---|
| Low event frequency or seasonal demand | A monthly subscription may be hard to justify | Test event-based purchase first; measure actual repeat use |
| Crew sees ASI:One as an extra app/account | Staff may continue taking work by phone and the system loses updates | Observe sign-in, offer acceptance, and completion with real crew during the pilot |
| Language or noisy-event communication | Reports may be unclear or misunderstood | Test the team's real language; confirm ambiguous category and location; retain text as a complete flow |
| Roster setup is inaccurate | Fast routing can still reach the wrong vendor | Have the organizer approve responsibility, staff eligibility, backups, and escalation authority before the event |
| Multi-day or high-issue events cost more | A flat fee can hide poor contribution | Measure invocation and support usage by day and event; define commercial limits only after observation |
| Existing tools already fit the planner | A new workflow adds switching cost | Compare a real incident against the existing process; keep only improvements the user values |

## Validation before scaling

1. **Interview three planners and one venue operator.** Ask each to reconstruct a recent real incident: who reported it, who owned it, how the owner accepted, how many follow-ups occurred, and how closure was confirmed. Ask who controls the budget and what they would need to approve a paid pilot.
2. **Observe one field pilot** with an approved event roster and willing staff. Record the baseline process and the EventRelay workflow. Separate synthetic tests from real incidents. Keep an organizer available for unclear, urgent, or unowned issues.
3. **Compare the same operational measures:** time to accountable acceptance, minutes without an owner, manual follow-ups, and reopened incidents. Also record setup/support minutes and actual usage cost.
4. **Make the decision from evidence.** Continue if coordinators need fewer follow-ups while accountability and closure quality hold up, staff actually participate, and the buyer accepts a viable paid offer. Iterate if setup, language, or ASI adoption blocks use. Do not scale on a polished demonstration alone.

One field pilot is directional evidence, not proof of broad demand or a reliable national savings percentage.
