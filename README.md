# data-retention-auditor

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GDPR Art. 5(1)(e)](https://img.shields.io/badge/GDPR-Art.%205(1)(e)-important)](docs/STORAGE_LIMITATION_GUIDE.md)

Scans data schemas for missing retention periods under UK GDPR Articles 5(1)(e), 17 and 30.

## The problem this solves

Under UK GDPR **Article 5(1)(e)**, personal data must not stay identifiable for longer than needed. Teams still ship tables with no retention metadata, a vague “as per policy”, and no deletion job — while the ROPA says something else.

**data-retention-auditor** reads a JSON schema inventory, scores personal-data fields against ICO-aligned checks, and exports findings — locally, with no cloud dependency and no live-database scan.

## Features

| Capability | Module | CLI mode |
| ---------- | ------ | -------- |
| JSON schema inventory | `parser.py` | `--input` |
| RET-01…08 rules engine | `engine.py` | `--mode scan` |
| Coverage score and FAIL / PARTIAL / PASS | `engine.py` | `--mode score` |
| Markdown + JSON + PDF export | `markdown_report.py` / `json_report.py` / `pdf_report.py` | `--mode report` |

## Installation

```bash
pip install -r requirements.txt
python main.py --help
python main.py --version
```

## Commands

| Mode | Required flags | What you get |
| ---- | -------------- | ------------ |
| `scan` | `--input schema.json` | Summary + findings table |
| `score` | `--input schema.json` | Band and score only |
| `report` | `--input`, optional `--output` | Terminal output + Markdown, JSON, and PDF |

### Examples

```bash
python main.py --mode scan --input sample_data/crm_leads.json
python main.py --mode score --input sample_data/hr_employees.json
python main.py --mode report --input sample_data/crm_leads.json --output outputs/
```

Output filenames use a sanitised `schema_id` stem (for example `CRM-001_findings.md`).

## Worked example — Harbour Sales CRM

A professional-services firm keeps inbound leads and website session replays. Email has no retention period. Source notes say “as per policy”. Replays claim 30 days with no deletion job.

```bash
python main.py --mode scan --input sample_data/crm_leads.json
```

Typical result on that inventory:

| Signal | Result |
| ------ | ------ |
| Personal-data fields | **3** |
| Score | **0.0 / 100** |
| Band | **FAIL** |
| Findings | **12** |

The HR sample (`sample_data/hr_employees.json`, aligned with ropa-builder activity `PA-001`) scores **100 / 100** and **PASS**.

### Sample output (Markdown excerpt)

Pre-generated artefacts: [`sample_outputs/`](sample_outputs/)

```text
Band: FAIL
Score: 0.0/100

leads.email              RET-01  FAIL     Missing retention period
leads.source_notes       RET-02  FAIL     Vague retention period
session_replays.blob     RET-04  PARTIAL  Retention not enforced
```

See [docs/STORAGE_LIMITATION_GUIDE.md](docs/STORAGE_LIMITATION_GUIDE.md) for rules and band definitions.

## GDPR coverage

| Article | Obligation | Handled by |
| ------- | ---------- | ---------- |
| Art. 5(1)(e) | Storage limitation | Period, trigger, disposal, deletion job, indefinite check |
| Art. 17 | Right to erasure | `erasure_supported` on personal-data fields |
| Art. 30(1)(f) | Envisaged time limits for erasure | Concrete period + optional `ropa_activity_id` |

## Repository structure

```text
data-retention-auditor/
├── main.py
├── src/auditor/          # parser and rules engine
├── src/reporter/         # Markdown, JSON, and PDF export
├── config/               # RET-01…08 rule JSON
├── sample_data/          # crm_leads.json (FAIL), hr_employees.json (PASS)
├── sample_outputs/       # committed demo reports
├── docs/                 # storage-limitation guide
└── tests/
```

## Limitations

- Decision-support only — not legal advice; a DPO should review outputs
- Detects missing and vague declarations, not whether a period is the right length
- Local CLI only — no live database, cloud sync, or production PII scan
- Scoring reflects this tool's methodology, not an ICO grade

## Licence

MIT. This tool is decision-support only and is not legal advice.
