# Google Ads Multi-Agent System (Universal Multi-Business Edition)

An autonomous multi-agent team designed in Google Antigravity to monitor, audit, and optimize a portfolio of 15+ Google Ads accounts across **any business type**: E-Commerce, B2B SaaS, Local Services, High-Ticket Lead Gen, Mobile Apps, Healthcare, and Info Products.

---

## 🏢 Universal Business Support

The system dynamically adapts its metrics, anomaly detection, negative keywords, and ad copy to the specific business model configured in `config/accounts.json`:

| Business Type | Primary KPI | Key Optimizations |
| :--- | :--- | :--- |
| **`ecommerce`** | **Target ROAS** / Revenue | Product margin tiers, PMax/Shopping signals, shopping negative keywords (disqualifies DIY/repair, preserves discount/store) |
| **`b2b_saas`** | **Target CPA** ($80 - $250+) | Demo/trial lead quality, offline conversion imports, negates students/jobs/internships/open-source |
| **`local_service`** | **Cost Per Call / CPA** | High CPC tolerance, phone call extensions, radius targeting, negates DIY and non-local queries |
| **`lead_gen`** | **Cost Per Qualified Lead** | Form conversion efficiency, pre-qualification, negates portal login/customer support queries |
| **`mobile_app`** | **Cost Per Install (CPI)** | In-app actions, app store rating proof, negates desktop/emulator/modded queries |
| **`healthcare`** | **Cost Per Appointment** | Doctor credentials, insurance acceptance, rapid online scheduling |
| **`info_product`** | **Front-End ROAS / CPA** | Course curriculum outcomes, VSL opt-ins, negates piracy/torrent searches |

---

## 👥 The Multi-Agent Team Roster

1. **Lead Coordinator**:
   - Scans all 15+ accounts using GAQL or deterministic cross-industry simulation.
   - Computes 7-day baselines (Spend, CPA, Conv, ROAS).
   - Evaluates dynamic zero-conversion thresholds (scaled to Target CPA, eliminating false positives).
   - Dispatches tailored tasks to specialized subagents and compiles the Master Staging Queue.

2. **Budget & Pacing Specialist** (`.agents/subagents/budget_pacing_agent.md`):
   - **Grounded in**: `ads` & `analytics`.
   - **Focus**: Evaluates budget pacing across both CPA and Target ROAS models. Scales budget to high-ROAS e-commerce campaigns and fixes overruns.

3. **Search Terms & Negative Keywords Miner** (`.agents/subagents/search_terms_agent.md`):
   - **Grounded in**: `ads` & `conversion-tracking`.
   - **Focus**: Eliminates zero-conversion spend bleed with model-specific negative keyword lists (disqualifies non-buyers without harming commercial traffic).

4. **Ad Copy & Creative Specialist** (`.agents/subagents/ad_creative_agent.md`):
   - **Grounded in**: `ad-creative` & `copywriting`.
   - **Focus**: Solves CPA spikes and ROAS drops. Generates 5 headlines (≤30 chars) and 2 descriptions (≤90 chars) strictly adhering to business-type angles with zero AI clichés.

---

## 📁 Directory Structure

```text
google-ads-manager/
├── google-ads.yaml                # Live MCC API credentials (gitignored)
├── google-ads.yaml.example        # Credential template for onboarding
├── config/
│   ├── accounts.json              # 15+ accounts with business_type, primary_metric & targets
│   └── thresholds.json            # Dynamic anomaly multipliers & industry negative presets
├── scripts/
│   ├── audit_accounts.py          # Universal metrics engine & executive reporter
│   ├── orchestrate_team.py        # Team coordinator & staging queue generator
│   └── setup_daily_schedule.ps1   # Least-privilege Windows scheduler registration (8:00 AM)
├── reports/
│   ├── audit_YYYY-MM-DD.csv       # Tabular spreadsheet with business type & ROAS columns
│   ├── summary_YYYY-MM-DD.md      # Executive performance overview
│   └── action_plan_YYYY-MM-DD.md  # Model-tailored Staging & Approval Queue
└── .agents/
    ├── product-marketing.md       # Global product marketing & business type context
    ├── skills/
    │   ├── google-ads-auditor/    # Core audit procedure skill
    │   └── google-ads-coordinator/# Multi-agent orchestration skill
    └── subagents/
        ├── budget_pacing_agent.md # Persona & prompt for Budget Specialist
        ├── search_terms_agent.md  # Persona & prompt for Keyword Miner
        └── ad_creative_agent.md   # Persona & prompt for Copy Specialist
```

---

## ⚡ How to Trigger the Multi-Agent Team

### Option A: On-Demand in Chat
Whenever you want the team to analyze your accounts, prompt Antigravity:
> *"Run multi-agent audit"* or *"Orchestrate ads team"*

The coordinator will scan your accounts, dispatch the subagents, and generate the daily [action_plan_YYYY-MM-DD.md](file:///d:/google-ads-manager/reports/).

### Option B: Scheduled Every Morning (8:00 AM)
- In chat, type `/schedule` or `/automation` to register a standing background schedule, OR
- Run [scripts/setup_daily_schedule.ps1](file:///d:/google-ads-manager/scripts/setup_daily_schedule.ps1) in PowerShell to register a Windows task.

---

## 🔒 Human-in-the-Loop Approval Queue
The agent system **never** applies changes blindly. It stages all changes in:
`reports/action_plan_YYYY-MM-DD.md`
with checkboxes:
- `[ ] Approve Budget Adjustment`
- `[ ] Approve Negative Keyword List`
- `[ ] Approve RSA Ad Copy`

Once reviewed and checked, tell the agent to proceed with applying approved items.
