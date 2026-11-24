---
name: google-ads-auditor
description: >-
  Use this skill to audit all 15+ Google Ads accounts, run daily morning performance checks,
  detect CPA spikes and zero-conversion budget waste, and propose tactical fixes using marketing skills.
---

# Google Ads Multi-Account Auditor

This skill provides step-by-step procedures for auditing and monitoring 15+ Google Ads accounts under a Manager Account (MCC).

## 1. Running the Audit
Execute the Python audit script:
```powershell
python scripts/audit_accounts.py
```

Outputs generated:
- `reports/audit_YYYY-MM-DD.csv`: Full spreadsheet of performance metrics across all 15+ accounts.
- `reports/summary_YYYY-MM-DD.md`: Executive brief highlighting red-flagged accounts and anomalies.

## 2. Diagnosing Anomalies
When the audit flags an account with a **RED FLAG**, cross-reference with the globally installed marketing skills:

### Case A: `ZERO_CONV_BLEED` (Spend without conversions)
- Evaluated dynamically against `target_cpa * multiplier` (preventing false alerts on high-ticket B2B while catching leaks on low-CPA accounts).
- Activate the **`ads`** skill.
- Query Search Terms report and apply model-specific negative keywords (e.g., exclude non-buyer intents for E-commerce; exclude career/job searches for B2B SaaS).
- Activate the **`conversion-tracking`** skill to verify tag firing.

### Case B: `ROAS_DROP` (E-Commerce & Retail Accounts)
- Triggered when ROAS drops >25% below `target_roas`.
- Audit product feed quality, price competitiveness, and Shopping/PMax asset group performance.
- Test promotional copy angles and exclude non-converting search queries.

### Case C: `CPA_SPIKE` (CPA increased >25% vs 7-day average)
- Check whether Conversion Rate (CvR) dropped or Cost-Per-Click (CPC) spiked.
- Activate the **`ad-creative`** skill to refresh ad copy, pin relevant headlines, and test new RSA variations.
- Inspect Quality Score trends.

### Case D: `BUDGET_OVERRUN` or `UNDERPACING`
- For overrun: Verify campaign budget delivery method and ensure automated rules or script caps are active.
- For underpacing: Check audience bid adjustments, search lost IS (budget vs rank), and keyword bid limits.

## 3. Account Configuration
- Edit `config/accounts.json` to update target CPAs, daily budgets, or account CIDs.
- Edit `config/thresholds.json` to calibrate sensitivity for anomaly alerts.
- Update live credentials in `google-ads.yaml`.
