# EventRelay — submission packet preparation

This packet is prepared for review. No project submission has been sent. Complete the live demonstration and missing evidence before presenting them as finished.

## Project name

**EventRelay — accountable event-day coordination across vendor teams**

## Brief description

EventRelay is designed for Indian weddings, birthdays, and similar events where a family, planner, venue, caterer, AV crew, and housekeeping team must coordinate temporary responsibilities. A report such as “there is a water issue” may need clarification before anyone knows whether catering, cleanup, or facilities should respond.

Through ASI:One, the coordinator is designed to collect the issue type and location, offer work to an eligible vendor, record explicit acceptance, follow up, escalate failed handoffs, and ask the reporter to confirm resolution. Four hosted vendor agents represent hospitality, audio, facilities, and housekeeping. The coordinator is the fifth hosted agent. Direct uAgent messages carry vendor offers and decisions; ACP and native cards keep the primary user workflow in ASI:One.

The intended executable outcome is a persistent issue record with an accountable accepted owner, recorded progress, and either reporter-confirmed closure or visible unresolved escalation. The demonstration event and staff are synthetic, and physical work is simulated. Current local/CI evidence and the remaining live verification gaps are documented in [VERIFICATION.md](VERIFICATION.md).

## Evidence links

| Item | Link or status |
|---|---|
| Public code and run/test instructions | [GitHub repository](https://github.com/sibiselvam2027-cpu/eventrelay-fetchathon) |
| Direct agent entry | [EventRelay Coordinator in ASI:One](https://asi1.ai/ai/agent1qw8wdau552av7vc7u0cgc4te3skntynvwkxay8244u995xcd67m32tjqmzu) |
| Public shared chat proving the complete workflow | **Pending.** The direct entry link above is not a shared-chat URL. |
| Demonstration video | **Pending.** Target length: 3–5 minutes; use [DEMO.md](DEMO.md). |
| Hosted agent addresses and profiles | [LIVE_DEPLOYMENT.md](LIVE_DEPLOYMENT.md); logged-out access remains a separate check |
| Business assumptions | [BUSINESS_MODEL.md](BUSINESS_MODEL.md) |

## Official submission workflow

Open the [Fetch-A-Thon dashboard](https://asi1.ai/festival/fetchathon3/dashboard?utm_source=fetchathon3), choose its **Project Submission Agent**, and follow its prompts. The [hackpack](https://www.fetch.ai/events/hackathons/fetch-a-thon-3/hackpack) documents code, public shared chat, profiles for submitted agents, video, and a problem/users/outcome description. Include agent names, addresses, run resources, and required badges in the relevant README information. Verify every link and the final acknowledgment.

The dashboard's exact current prompts could not be read through the public fetch: it redirected to a sign-in-paused page. No extra form fields or submission success are invented here.

## Timing and final check

The public schedule lists 16:30 IST for final building/submission, followed by 17:50 closing and 18:00 event end. It asks entrants to meet the announced deadline without publishing an explicit submission cutoff. The team's 16:45 demo target is therefore separate from the official deadline, which still needs confirmation from the current dashboard or organizer announcement.

Before submitting, use [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) to distinguish passing code tests, hosted startup, ACP delivery, genuine agent replies, and the complete live workflow. No external messages or actual submission were performed while preparing this packet.
