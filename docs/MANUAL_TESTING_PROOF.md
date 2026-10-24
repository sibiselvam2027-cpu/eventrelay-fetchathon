# Agentverse Manual Testing — completed native workflow

**Completed: 24 October 2026, 17:55:05 IST (12:25:05 UTC).** The organizer-recommended **Agent Profile → Testing → Manual Testing** route completed synthetic wedding incident **ER-3CC6223A** with native form/card interactions.

## Observed sequence

1. The coordinator returned its help response.
2. An explicitly labelled AI-unavailable guided form requested the category and location. The operator submitted those fields through the native form; no successful LLM reasoning is claimed for this step.
3. The actual hosted hospitality agent supplied its configured synthetic **Arun decline → Neha acceptance** decisions. The presenter did **not** click Accept.
4. Native **Start work** and **Report completed** actions moved the incident to **awaiting reporter confirmation**.
5. Native **Still a problem** reopened the **same incident ID**. A subsequent vendor acceptance was recorded.
6. Native **Start work** and **Report completed** were submitted again.
7. Native **Yes, resolved** closed the incident after reporter confirmation, with its activity history retained.

The rehearsal preserved the same reporter identity and conversation session through clarification, worker simulation, reopening, and closure. All tested form and card callbacks completed. No unrecorded state version or intermediate timestamp is inferred.

## What this proves

The hosted workflow completed through an actual Agentverse UI, including guided category/location capture, real hosted vendor-agent decisions, native callback handling, persistent ownership, same-ID reopening, and reporter-confirmed closure. It supplements the earlier four-category hosted rehearsals in [LIVE_WORKFLOW_PROOF.md](LIVE_WORKFLOW_PROOF.md).

## Evidence boundaries

People, configured staff decisions, progress updates, physical work, and the demonstration event were synthetic. No real crew contact or physical repair is claimed. This was **Agentverse Manual Testing**, not the ASI:One web interface. Full ASI:One web completion and a public ASI:One shared chat remain pending recovery. Video encoding is separate from this successful rehearsal.

This sanitized record was checked against the retained manual-demo proof. Screenshots, the raw transcript, account details, organizer identity/contact information, credentials, and private session identifiers are excluded from this public document.
