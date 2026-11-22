# Contributing to Google Ads Multi-Agent System

Thank you for your interest in contributing! This project helps marketing teams, agencies, and developers audit and optimize multi-account Google Ads portfolios using domain-expert AI subagents.

---

## Getting Started

1. **Fork and clone** this repository.
2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. **Run tests**:
   ```bash
   python -m unittest discover tests
   ```

---

## How to Contribute

### 1. Adding a New Business Profile
We welcome new industry profiles! To add a business model:
1. Open `config/thresholds.json`.
2. Add your business type under `business_type_profiles` (e.g., `"real_estate"`, `"dental_clinic"`, `"auto_dealership"`).
3. Include appropriate `negative_keyword_disqualifiers`, `primary_metric`, and `zero_conversion_spend_cpa_multiplier`.
4. Add tailored RSA headline and description generation rules in `scripts/orchestrate_team.py`.
5. Add unit tests in `tests/test_audit.py` to confirm headlines stay $\le 30$ chars and descriptions $\le 90$ chars.

### 2. Improving Subagents
Our subagents follow strict marketing principles:
- **Zero AI Clichés**: Never add templates using phrases like *"Say goodbye to"*, *"In today's fast-paced world"*, or *"It's not X, it's Y"*.
- **Human-in-the-Loop**: Agents never directly apply unreviewed mutations; all changes must pass through the staging queue.

---

## Pull Request Checklist

Before submitting a PR, please verify:
- [ ] Unit tests pass: `python -m unittest discover tests`
- [ ] Sample audit works: `python scripts/audit_accounts.py --sample`
- [ ] Orchestrator runs: `python scripts/orchestrate_team.py --sample`
- [ ] No API keys, credentials, or personal secrets are included in commits.
