# Storage limitation guide — Articles 5(1)(e), 17 and 30

Plain-English overview of UK GDPR **storage limitation** and how this CLI checks a data schema for missing or unenforced retention metadata.

## Why this matters

Article 5(1)(e) says personal data must not stay identifiable for longer than needed for the stated purpose. The ICO does **not** set a universal clock. You choose and justify periods, document them, and erase or anonymise when they end.

In practice the gap is not the policy Word doc. It is the schema: tables and fields that hold personal data with no period, a vague “as per policy”, no trigger event, and no deletion job. This tool scans a **declared inventory**, not a live database.

## What the law asks for

| Source | Obligation | What this tool looks for |
| ------ | ---------- | ------------------------ |
| Art. 5(1)(e) | Keep personal data no longer than necessary | A period, a trigger, a disposal action, and a deletion job |
| Art. 30(1)(f) | Record envisaged time limits for erasure | A concrete period on the field, linked to a ROPA activity |
| Art. 17 | Right to erasure where the data is no longer needed | `erasure_supported` on personal-data fields |
| Art. 89 | Longer retention only for archiving, research, or statistics | `art89_exception` required if the period is indefinite |

The ICO also expects a retention schedule, regular review, and a process for erasure requests. This CLI does not replace that schedule. It flags schema fields that would fail a first look.

Pointers such as “in accordance with the retention policy” are not a period. Say **30 days after last contact**, not “see policy”.

## How scoring works

Only fields with `personal_data: true` are scored. Internal keys are ignored.

Start at **100**. Each finding subtracts its weight. Bands (decision-support labels, not an ICO grade):

| Band | Rule |
| ---- | ---- |
| **FAIL** | Any FAIL finding, or score below 50 |
| **PARTIAL** | Only PARTIAL findings remain |
| **PASS** | No findings |
| **PARTIAL** (no score) | Inventory has no personal-data fields |

| ID | Condition | Severity |
| -- | --------- | -------- |
| RET-01 | Empty `retention_period` | FAIL |
| RET-02 | Vague period (`as per policy`, `tbd`, `n/a`, …) | FAIL |
| RET-03 | Usable period but no trigger event | PARTIAL |
| RET-04 | Usable period but `deletion_job` is not true | PARTIAL |
| RET-05 | No disposal (`erase` or `anonymise`) | PARTIAL |
| RET-06 | `erasure_supported` is not true | FAIL |
| RET-07 | Indefinite period without `art89_exception` | FAIL |
| RET-08 | No `ropa_activity_id` | PARTIAL |

Placeholders (`n/a`, `as per policy`) on trigger, disposal, or ROPA id count as empty. “Permanent staff” is not treated as indefinite retention; “kept permanently” is.

## How to use this tool

1. Describe tables and fields in JSON (`sample_data/` has a FAIL CRM and a PASS HR register).
2. Run a mode:
   - `scan` — terminal summary and findings table
   - `score` — band and score only
   - `report` — also writes Markdown, JSON, and PDF
3. Fix the schema (and the ROPA) from the findings. Re-run until the band is acceptable to the DPO.

```bash
python main.py --mode scan --input sample_data/crm_leads.json
python main.py --mode report --input sample_data/hr_employees.json --output outputs/
```

## Limitations

- Detects missing and vague **declarations**. It does not judge whether “7 years” is the right length.
- Does not connect to production databases or scan live personal data.
- Does not write a ROPA. Link fields with `ropa_activity_id` to keep the schema and Article 30 record aligned.
- Decision-support only. Not legal advice. A DPO should review outputs.

Further reading: [ICO, Principle (e): Storage limitation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/).
