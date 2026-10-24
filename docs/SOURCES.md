# Sources and claim boundaries

Reviewed for the EventRelay competition concept on **24 October 2026**. Product and fundraising pages are first-party descriptions; they do not independently establish market size, adoption, or willingness to pay for EventRelay.

| Source | What it supports | What it does not establish |
|---|---|---|
| [Fetch-A-Thon 3.0 hackpack](https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack) | Challenge, judging weights, required ecosystem integration, submission materials | That any particular idea will win |
| [Agentverse: Agent-Driven Interactive Cards](https://docs.agentverse.ai/documentation/advanced-usages/agent-driven-interactive-cards) | Native conversational cards and callback behavior | That the POC's card flow has been tested in a live ASI chat |
| [Agentverse: Hosted Agents](https://docs.agentverse.ai/documentation/create-agents/hosted-agents) | Hosted agents reset globals between invocations; persistent state belongs in Agent Storage; profile and protocol setup remain part of discovery | That the EventRelay hosted implementation, five deployments, or ASI workflow are already verified |
| [Agentverse: Hosted Code Editor](https://docs.agentverse.ai/documentation/create-agents/hosted-code-editor) | Hosted multi-file modules, Agent Secrets, Storage, and Logs | That locally supported packages or persistence mechanisms automatically work in the hosted environment |
| [Halo Solutions](https://www.halosolutions.com/) | Existing event/venue incident, task, team, and location management | A unique EventRelay category or a validated India-specific gap |
| [Halo terminology guide](https://academy.halosolutions.com/halo-terminology-guide) | Existing incident and task lifecycles, including assignment and closure | That lifecycle tracking alone is novel |
| [All Things Wed](https://allthingswed.com/) | An existing platform for professional wedding planners in India with tasks, vendors, team, and customer views | That Indian wedding teams lack all software alternatives |
| [Meta: managing business chats on WhatsApp](https://about.fb.com/news/2025/04/ways-to-manage-your-businesses-chats-on-whatsapp/) | Business messaging has its own recipient expectations and template-based initiation flow | That EventRelay currently sends WhatsApp messages or calls |

## EventRelay-specific claims requiring our own evidence

- Correct routing for an event's actual responsibility roster.
- Explicit worker acceptance rather than transport acknowledgment.
- Backup routing, timeout handling, and honest unresolved escalation.
- Separate crew completion and reporter-confirmed closure.
- Authentication and permission checks for staff and reporters.
- Measured reliability of the live ASI:One workflow.
- Benefits relative to a planner's present communication process.

All names, staffing rules, response timers, and physical work used in the demonstration are synthetic or configured test data unless expressly documented otherwise. No interviews, deployed customers, financial results, or time savings are claimed.

The approved architecture is five Agentverse Hosted Agents—coordinator, hospitality, audio, facilities, and housekeeping—with ASI:One as the sole user interface and direct uAgents/ACP interaction. It does not use a custom frontend, LangChain, or MCP. Hosted implementation tests, deployments, message exchanges, state persistence, and ASI discovery remain pending until verified; they are not claims derived from these sources.

The local verification baseline is Python 3.12 and uAgents 0.25.5. Hosted runtime compatibility is a separate verification item. The pricing options in [BUSINESS_MODEL.md](BUSINESS_MODEL.md) are unvalidated hypotheses, not sourced market prices or existing revenue.
