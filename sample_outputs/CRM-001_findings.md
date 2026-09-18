# Retention audit: Harbour Sales CRM

- Schema ID: `CRM-001`
- Organisation: Harbour Advisory LLP
- Personal-data fields: 3
- Score: **0.0/100**
- Band: **FAIL**
- Findings: 12

**Notes:** Worked FAIL example. Marketing and sales data with missing or vague retention metadata.

| Location | Rule | Severity | Articles | Issue |
| -------- | ---- | -------- | -------- | ----- |
| leads.email | RET-01 | FAIL | Art. 5(1)(e), Art. 30(1)(f) | Missing retention period |
| leads.email | RET-05 | PARTIAL | Art. 5(1)(e) | No disposal action |
| leads.email | RET-06 | FAIL | Art. 17 | Erasure not supported |
| leads.email | RET-08 | PARTIAL | Art. 30 | No ROPA activity link |
| leads.source_notes | RET-02 | FAIL | Art. 5(1)(e), Art. 30(1)(f) | Vague retention period |
| leads.source_notes | RET-05 | PARTIAL | Art. 5(1)(e) | No disposal action |
| leads.source_notes | RET-06 | FAIL | Art. 17 | Erasure not supported |
| leads.source_notes | RET-08 | PARTIAL | Art. 30 | No ROPA activity link |
| session_replays.blob | RET-03 | PARTIAL | Art. 5(1)(e) | No trigger event |
| session_replays.blob | RET-04 | PARTIAL | Art. 5(1)(e) | Retention not enforced |
| session_replays.blob | RET-06 | FAIL | Art. 17 | Erasure not supported |
| session_replays.blob | RET-08 | PARTIAL | Art. 30 | No ROPA activity link |

## Remediation

- **leads.email** (`RET-01`): Declare a retention period with a trigger event for this personal-data field, then record it on the ROPA.
- **leads.email** (`RET-05`): Record whether the field is erased or anonymised when the period ends.
- **leads.email** (`RET-06`): Confirm the field can be deleted or put beyond use so Article 17 requests can be met.
- **leads.email** (`RET-08`): Map the field to an Article 30 processing activity id so the schema and the ROPA stay aligned.
- **leads.source_notes** (`RET-02`): Replace pointers such as 'as per policy' with a concrete period and trigger (for example '30 days after last contact').
- **leads.source_notes** (`RET-05`): Record whether the field is erased or anonymised when the period ends.
- **leads.source_notes** (`RET-06`): Confirm the field can be deleted or put beyond use so Article 17 requests can be met.
- **leads.source_notes** (`RET-08`): Map the field to an Article 30 processing activity id so the schema and the ROPA stay aligned.
- **session_replays.blob** (`RET-03`): State when the clock starts (end of employment, last appointment, account closure), not only a duration.
- **session_replays.blob** (`RET-04`): Add an automated deletion or anonymisation job so the declared period is kept in practice.
- **session_replays.blob** (`RET-06`): Confirm the field can be deleted or put beyond use so Article 17 requests can be met.
- **session_replays.blob** (`RET-08`): Map the field to an Article 30 processing activity id so the schema and the ROPA stay aligned.

---
Decision-support only. Not legal advice.
