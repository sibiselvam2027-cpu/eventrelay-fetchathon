# Live hosted workflow proof — four synthetic event incidents

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

**Not established by the water test alone:** ASI:One frontend operation, live LLM extraction, the complete user-facing ASI:One workflow, public shared-chat evidence, or other vendor categories. The additional rehearsal below supplies separate evidence for all four service categories and one natural-language status lookup. It still does not replace the competition's ASI:One demonstration requirement.

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

## Additional hosted rehearsal — completed by 16:25:07 IST

The actual hosted coordinator exchanged offers and decisions with the audio, facilities, and housekeeping agents. Their configured synthetic policies supplied acceptance; the diagnostic reporter did not accept work on their behalf.

| Incident | Actual vendor agent / synthetic owner | Observed progression |
|---|---|---|
| Audio `ER-3B225E95` | Audio / Ravi | Accepted v3 → in progress v4 → awaiting confirmation v5 → reporter requested reopening → **same issue** accepted v8 → in progress v9 → awaiting confirmation v10 → closed. |
| Power `ER-CB20232F` | Facilities / Vikram | Accepted v3 → in progress v4 → awaiting confirmation v5 → closed. |
| Cleanup `ER-5C25C933` | Housekeeping / Meena | Accepted v3 → in progress v4 → awaiting confirmation v5 → closed. |

All three closures were observed by **16:25:07 IST**. Individual earlier audio/power closure timestamps were not retained in the available log window. Final confirmation cards did not supply a version, so no closed-state version is inferred.

A plain-language probe, **“show status of ER-A50BFBB4”**, returned the actual stored **closed** water issue through the hosted ASI1 intent-extraction path without the earlier authentication error. This verifies that status lookup, not unrestricted natural-language understanding or an entire natural-language report/clarification flow.

The prompt was sent at **16:24:39.675 IST** and its response arrived at **16:25:07.261 IST** in the current rehearsal session, separate from the earlier water session. The current diagnostic sent no structured water-status request. The captured response excerpt included `Status: closed` and `Accountable owner: Neha`; it began with the demonstration-data label rather than the offline-parser label. The prompt also does not match the hosted explicit-command parser, supporting the recorded ASI1 extraction path. Only the captured excerpt is retained; the remaining reply is not reconstructed.

**Combined verified scope:** all five product roles participated in the tested hosted workflows; four service categories reached persistent closure; the audio incident reopened and reaccepted under the same ID; the water incident used decline-to-backup routing; one natural-language status lookup succeeded.

**Remaining limits:** all people, configured staff decisions, physical work, progress actions, and reporter confirmations were synthetic. ASI:One frontend completion, native-form rendering, public shared-chat evidence, live role-restriction/stale-action checks, and real-world service outcomes remain separate verification items.
