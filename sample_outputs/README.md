# Sample outputs

Pre-generated reports from the committed schema inventories so visitors can inspect artefacts without running the tool.

Regenerate with:

```bash
python main.py --mode report --input sample_data/crm_leads.json --output sample_outputs/
python main.py --mode report --input sample_data/hr_employees.json --output sample_outputs/
```

Files:

- `CRM-001_findings.md` / `.json` / `_report.pdf` — Harbour Sales CRM (FAIL)
- `HR-001_findings.md` / `.json` / `_report.pdf` — Example Healthcare Trust (PASS)
