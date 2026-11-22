---
name: google-ads-coordinator
description: >-
  Use this skill to orchestrate the multi-agent Google Ads team across 15+ accounts.
  Coordinates the Lead Coordinator, Budget Specialist, Search Terms Miner, and Ad Creative Specialist
  to produce the daily Staging & Approval Queue artifact.
---

# Google Ads Multi-Agent Coordinator

This skill defines the orchestration workflow for the multi-agent Google Ads team.

## Team Roster
- **Lead Coordinator**: Scans all 15+ accounts, flags anomalies, and synthesizes the master plan.
- **Budget & Pacing Specialist** (`.agents/subagents/budget_pacing_agent.md`):
  - Uses skills: `ads` and `analytics`.
  - Solves budget overruns and underpacing.
- **Search Terms & Negative Keywords Miner** (`.agents/subagents/search_terms_agent.md`):
  - Uses skills: `ads` and `conversion-tracking`.
  - Solves zero-conversion spend bleed by staging exact & phrase negative keyword lists.
- **Ad Copy & Creative Specialist** (`.agents/subagents/ad_creative_agent.md`):
  - Uses skills: `ad-creative` and `copywriting`.
  - Solves CPA spikes and ad fatigue by writing high-converting RSA copy without AI clichés.

## How to Run
Whenever the user asks to:
- *"Run multi-agent audit"*
- *"Orchestrate ads team"*
- *"Review daily action plan"*

Execute the team orchestrator:
```powershell
python scripts/orchestrate_team.py
```

Then present the generated [action_plan_YYYY-MM-DD.md](file:///d:/google-ads-manager/reports/) to the user as a staging queue for their approval.
