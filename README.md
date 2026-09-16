# data-retention-auditor

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GDPR Art. 5(1)(e)](https://img.shields.io/badge/GDPR-Art.%205(1)(e)-important)](https://www.legislation.gov.uk/eur/2016/679/article/5)

Scans data schemas for missing retention periods under UK GDPR Articles 5(1)(e), 17 and 30.

This repository is a scaffold. The scanner and reports are not implemented yet.

JSON schema inventories live in `sample_data/`:

- `crm_leads.json` — sales CRM with missing and vague retention metadata
- `hr_employees.json` — HR records with period, trigger, disposal, and a ROPA link

## Planned CLI

```bash
pip install -r requirements.txt
python main.py --help
python main.py --version
```
