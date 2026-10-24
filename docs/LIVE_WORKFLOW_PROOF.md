# Live hosted workflow proof — synthetic drinking-water incident

**Observed closure: 24 October 2026, 16:16:19 IST.** A temporary diagnostic observer exchanged structured ACP messages with the hosted coordinator. The coordinator and hospitality agents exchanged actual typed uAgent offers and decisions on Agentverse. The observer is not a sixth product role.

## Observed result

Incident **ER-A50BFBB4** belonged to the synthetic `wedding-demo` event, category `drinking_water`, location `Dining Hall`. The issue progressed in the same ACP session:

| Observed state | Recorded version | What happened |
|---|---:|---|
| Offered | 2 | An offer awaited the primary hospitality worker's decision. |
| Backup offered | 4 | The configured primary-decline response triggered a backup offer. |
| Accepted | 5 | The hospitality agent returned its configured acceptance for Neha. |
| In progress | 6 | A synthetic diagnostic progress action was recorded. |
| Awaiting confirmation | 7 | Synthetic crew completion was recorded without automatically closing the issue. |
| Closed | — | Synthetic reporter confirmation closed the persistent issue at 16:16:19 IST. |

The acceptance came from the actual hospitality agent's explicitly configured simulator policy: Arun declined and Neha accepted. The diagnostic observer **did not click Accept**. Actual hosted agent-to-agent requests and decisions therefore occurred; a transport acknowledgment was not treated as staff acceptance.

## Evidence boundaries

**Verified by this rehearsal:** hosted coordinator/hospitality transport, primary-decline-to-backup routing, an explicit vendor acceptance, persistent lifecycle updates across messages, and final closure of the same issue.

**Simulated:** staff identities, their configured decisions, physical work, progress updates, and reporter confirmation. No real worker contact or physical repair is claimed.

**Still unverified by this test:** ASI:One frontend operation, live LLM extraction, the complete user-facing ASI:One workflow, public shared-chat evidence, and the other vendor categories. Those require separate tests. A successful structured-message rehearsal is not substituted for the competition's ASI:One demonstration requirement.

## Sanitized evidence summary

```json
{
  "issue_id": "ER-A50BFBB4",
  "event_id": "wedding-demo",
  "category": "drinking_water",
  "location": "Dining Hall",
  "closed_at_ist": "2026-10-24T16:16:19.875+05:30",
  "real_agentverse_hosted_transport_verified": true,
  "persistent_workflow_closure_verified": true,
  "vendor_acceptance_source": "Configured synthetic policy of the actual hospitality agent",
  "physical_work_and_reporter_confirmation": "Explicitly synthetic diagnostic actions",
  "asi_ui_verified": false,
  "llm_extraction_verified": false
}
```

This summary was checked against the retained rehearsal proof and logs. Raw credentials, environment values, sender credentials, and private runtime files are excluded from the public evidence.
