# EventRelay submission guardrail checklist

This separates the [official mandatory requirements](https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack) from extra rehearsals and final submission actions. The implemented prototype is demonstrated; final competition submission has not been sent.

## Mandatory technical eligibility

| Requirement | Verified evidence | Status |
|---|---|---|
| At least one Agentverse agent | Five hosted product identities and four-category message exchanges | Complete |
| Agent Chat Protocol | Published ChatMessage/ChatAcknowledgement handlers and actual ASI:One interactions | Complete |
| ASI:One discovery and direct use | Address profile, name-level recipient lookup, fresh `help` at 19:59 IST | Complete |
| Meaningful execution or multi-agent orchestration | Vendor offers/decisions, accountable acceptance, persistent issue state and follow-up | Complete |
| Complete primary workflow in ASI:One | ER-4DE240CA report, acceptance, work, reopening, reacceptance and confirmed closure | Complete |
| Public GitHub with run/test instructions | [Repository](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon), 83 passing source/CI tests and hosted builds | Complete |

The code uses direct uAgents with no custom product frontend. All five hosted README files contain the Innovation Lab and hackathon badges. The root README lists all five names, addresses, and profile URLs. ASI:One forms/cards provide the demonstrated user interactions.

## Required evidence and submission assets

- [x] [Public ASI:One shared-chat URL](https://asi1.ai/shared-chat/69fc8518-55f8-4b17-bd88-59988ba627f7) created through Share and opened in its read-only viewer. Follow ER-4DE240CA at approximately 18:32–18:44 IST.
- [x] Actual Agentverse profile URLs for all five submitted agents listed in [SUBMISSION_PACKET.md](SUBMISSION_PACKET.md).
- [x] Public source, test instructions, names/addresses, and required badges.
- [x] Brief problem, target users, and executable outcome description.
- [x] Requested [PowerPoint](EventRelay-pitch.pptx), covering the product and agent use cases.
- [ ] **Team-provided:** accessible 3–5 minute video URL. The hackpack requests a video even though the live form labels it optional.
- [ ] Final review of every profile/media link in the reviewer's intended access mode. Separate signed-out access to every Agentverse profile is not claimed.

The live official form additionally marks **PPT URL required**. The user requested the deck after that readback. Team registration and location were validated; private team/contact details are excluded from this public checklist.

## Final submission

- [x] Open the official dashboard and Project Submission agent.
- [x] Validate the registered Team ID/location and prepare known project/contact fields in the private form.
- [x] Add the published public PPT URL to the private form. The form is prepared in the current browser tab; Submit project remains untouched.
- [ ] Team adds its video URL and completes the final review.
- [ ] Press Submit project through the official agent when the reviewed packet is ready.
- [ ] Retain the final submission acknowledgment. **No final submission or receipt is claimed.**

## Scoring additions and prototype limits

Multi-agent collaboration and native interactive cards are implemented. **Payment Protocol is not implemented**; the hackpack lists it for additional consideration rather than mandatory eligibility. The per-event pilot/subscription model is a business hypothesis.

The demo uses synthetic staff, configured vendor decisions, and simulated physical work. ASI:One showed rendering delays, and a repeated old action produced a stale-version warning. Stable request IDs protect transport retries; a new semantically similar report can create another issue. Actual staff participation, every language case, live authorization-negative scenarios, and a real-event pilot remain additional validation work. These are not silently marked as completed by the 83 source tests.

Use the [Audio/Stage test guide](QUICK_DEMO.md) in a separate conversation. Fresh `help` at 19:59 IST and `roster` at 20:00 IST passed; Ravi was available at that point. Read the current roster before another run. Keep one issue and reporter conversation through closure.

The team-supplied organizer announcement extends submission to **11:59 PM IST, 24 October 2026**, and recommends Agentverse Manual Testing during disruption. The [completed Manual Testing rehearsal](MANUAL_TESTING_PROOF.md) is separately labelled.
