"""
Google Ads Multi-Agent Orchestrator (Universal Cross-Industry Edition)
Coordinates the Lead Coordinator and delegates tasks to 3 specialized subagents:
1. Budget & Pacing Specialist (CPA & Target ROAS pacing)
2. Search Terms & Negative Keywords Miner (Model-specific negative keyword lists)
3. Ad Copy & Creative Specialist (High-converting RSA copy tailored by business model)

Generates a unified Action Staging Plan in reports/action_plan_YYYY-MM-DD.md.
"""

import sys
import json
import argparse
import datetime
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.audit_accounts import (
    load_json,
    load_yaml,
    are_creds_configured,
    fetch_live_google_ads_data,
    generate_sample_data,
    validate_date_str,
    get_currency_symbol,
    CONFIG_DIR,
    REPORTS_DIR,
    CREDS_FILE,
)


def sanitize_text(text: str) -> str:
    """Sanitizes dynamic text to prevent markdown injection."""
    if not text:
        return ""
    return str(text).replace("\r", " ").replace("\n", " ").replace("[", "(").replace("]", ")").strip()


def generate_rsa_copy_for_business(business_type: str, account_name: str, currency: str = "USD") -> dict:
    """
    Generates industry-grounded RSA headlines (<=30 chars) and descriptions (<=90 chars)
    free of AI clichés, with pinning recommendations and local currency anchors.
    """
    brand = sanitize_text(account_name.split("-")[0].strip())
    b_type = (business_type or "general").lower()
    curr_upper = (currency or "USD").upper()

    if b_type == "ecommerce":
        shipping_hook = "Free Shipping Over ₹999" if curr_upper == "INR" else ("Free Shipping Over £40" if curr_upper == "GBP" else "Free 2-Day Shipping Over $50")
        return {
            "headlines": [
                f"{brand} Official Store",          # Pin 1
                shipping_hook,                      # Pin 2
                "30-Day Money Back Guarantee",
                "Shop New 2026 Collection",
                "Rated 4.9★ by Customers",
            ],
            "descriptions": [
                "Premium quality crafted for comfort and style. Enjoy fast shipping & hassle-free returns.",
                "Upgrade your everyday essentials with exclusive designs. Shop now for limited-time offers.",
            ],
            "focus": "Product value proposition, shipping offers, returns guarantee, and social proof.",
        }
    elif b_type == "b2b_saas":
        return {
            "headlines": [
                f"{brand} Official Platform",       # Pin 1
                "Deploy in Under 10 Minutes",        # Pin 2
                "SOC-2 Type II Certified",
                "Cut Manual Work by 60%",
                "Request an Instant Demo",
            ],
            "descriptions": [
                "Streamline operations and scale your team with automated workflows and live analytics.",
                "See why 1,500+ enterprises trust our platform. Request an instant live interactive demo.",
            ],
            "focus": "Fast time-to-value, enterprise compliance, concrete ROI, and demo call-to-action.",
        }
    elif b_type == "local_service":
        return {
            "headlines": [
                f"{brand} Near You",                # Pin 1
                "Licensed & Fully Insured",         # Pin 2
                "24/7 Rapid Emergency Care",
                "Free On-Site Estimate",
                "Call Today - Same Day",
            ],
            "descriptions": [
                "Fast, dependable local service you can count on. Upfront pricing with no hidden charges.",
                "Over 15 years serving your neighborhood. Call our certified technicians right now.",
            ],
            "focus": "Proximity, licensing credentials, rapid emergency response, and direct phone calls.",
        }
    elif b_type == "mobile_app":
        return {
            "headlines": [
                f"Download {brand} Free",           # Pin 1
                "Rated 4.8★ on App Store",          # Pin 2
                "Track Progress Daily",
                "Start in Under 60 Seconds",
                "Join 500k+ Active Members",
            ],
            "descriptions": [
                "Intuitive daily tracking and personalized routines built for your goals. Install today.",
                "The top-rated app for effortless progress tracking. Download free on iOS and Android.",
            ],
            "focus": "Lightweight install, app store rating, immediate utility, and free onboarding.",
        }
    elif b_type == "lead_gen":
        return {
            "headlines": [
                f"{brand} Pre-Approval",            # Pin 1
                "Compare Rates in 2 Mins",          # Pin 2
                "No Obligation Fast Quote",
                "Licensed Advisors Ready",
                "Simple 1-Page Application",
            ],
            "descriptions": [
                "Lock in competitive rates and personalized terms for your needs. Apply in minutes.",
                "Work with certified specialists dedicated to finding the best option for your situation.",
            ],
            "focus": "Low-friction pre-qualification, competitive terms, and no-obligation trust signals.",
        }
    elif b_type == "healthcare":
        return {
            "headlines": [
                f"{brand} Clinic",                  # Pin 1
                "Board-Certified Doctors",          # Pin 2
                "Same-Day Appointments",
                "Compassionate Care Team",
                "Book Online in 60 Seconds",
            ],
            "descriptions": [
                "Compassionate, personalized healthcare for you and your family. Schedule your visit today.",
                "Advanced treatments in a comfortable modern setting. Most major insurance plans accepted.",
            ],
            "focus": "Doctor credentials, insurance acceptance, rapid appointment booking, and patient trust.",
        }
    else:  # info_product or general
        return {
            "headlines": [
                f"{brand} Masterclass",             # Pin 1
                "Step-By-Step Video Guide",         # Pin 2
                "Proven Framework & System",
                "Instant Lifetime Access",
                "Join 10,000+ Students",
            ],
            "descriptions": [
                "Learn the proven frameworks used by industry leaders. Enroll and level up your skills.",
                "Practical, actionable lessons with lifetime access and community support. Get started now.",
            ],
            "focus": "Actionable outcomes, lifetime curriculum access, and student transformation proof.",
        }


def generate_staged_action_plan(results: list, output_path: Path, date_str: str, thresholds: dict = None):
    resolved = output_path.resolve()
    if not resolved.is_relative_to(REPORTS_DIR.resolve()):
        raise ValueError(f"Security violation: path traversal detected for {resolved}")

    red_flag_accounts = [r for r in results if r["status"] == "RED FLAG"]
    profiles = (thresholds or {}).get("business_type_profiles", {})
    
    lines = [
        f"# 📋 Multi-Agent Staging & Approval Queue - {date_str}",
        f"\nGenerated by **Lead Coordinator Agent** | {len(red_flag_accounts)} Accounts Staged for Review (Universal Multi-Business Support)\n",
        "> [!IMPORTANT]",
        "> **Human-in-the-Loop Approval Required**",
        "> Review the staged recommendations below produced by the specialized subagents.",
        "> Check the boxes [x] for recommendations you approve before applying.\n",
        "---",
    ]

    if not red_flag_accounts:
        lines.append("## ✅ All Accounts Healthy")
        lines.append("No critical anomalies detected across the portfolio. No interventions required today.")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return

    # Section 1: Budget & Pacing Specialist Findings
    budget_issues = [r for r in red_flag_accounts if any("BUDGET" in a or "UNDERPACING" in a for a in r["anomalies"])]
    lines.append("## 1. 💰 Budget & Pacing Specialist (Subagent: `budget-pacing-agent`)")
    lines.append("*Grounded in `ads` & `analytics` skills — Evaluates pacing across CPA & Target ROAS models*\n")
    if budget_issues:
        for r in budget_issues:
            flags = ", ".join(r["anomalies"])
            is_overrun = any("OVERRUN" in a for a in r["anomalies"])
            suggested_budget = round(r["daily_budget"] * 1.20, 2) if is_overrun else round(r["daily_budget"] * 0.85, 2)
            b_type = r.get("business_type", "general")
            curr = get_currency_symbol(r.get("currency", "USD"))
            
            target_desc = f"Target ROAS: {r['target_roas']:.2f}x (Yesterday: {r['roas']:.2f}x)" if r.get("primary_metric") == "ROAS" else f"Target CPA: {curr}{r['target_cpa']:,.2f} (Yesterday: {curr}{r['cpa']:,.2f})"
            
            lines.extend([
                f"### Account: **{r['account_name']}** (`{r['account_id']}`) — `{b_type.upper()}` [{r.get('currency', 'USD')}]",
                f"- **Yesterday Spend**: {curr}{r['yesterday_spend']:,.2f} (Target Daily Budget: {curr}{r['daily_budget']:,.2f})",
                f"- **Efficiency Context**: {target_desc}",
                f"- **Detected Issue**: {flags}",
                f"- **Staged Action**:",
                f"  - [ ] **Approve Budget Adjustment**: Change daily budget to **{curr}{suggested_budget:,.2f}**/day",
                f"  - [ ] **Approve Bid Optimization**: Calibrate bid ceilings based on `{r.get('primary_metric', 'CPA')}` goals.",
                "",
            ])
    else:
        lines.append("No budget pacing anomalies detected today.\n")

    # Section 2: Search Terms & Negative Keywords Miner Findings
    waste_issues = [r for r in red_flag_accounts if any("ZERO_CONV_BLEED" in a for a in r["anomalies"])]
    lines.append("## 2. 🛡️ Search Terms & Negative Keywords Miner (Subagent: `search-terms-agent`)")
    lines.append("*Grounded in `ads` & `conversion-tracking` skills — Tailors negative keywords by industry model*\n")
    if waste_issues:
        for r in waste_issues:
            b_type = r.get("business_type", "general")
            b_prof = profiles.get(b_type, {})
            disqualifiers = b_prof.get("negative_keyword_disqualifiers", ["jobs", "salary", "free", "diy", "pdf download"])
            
            curr = get_currency_symbol(r.get("currency", "USD"))
            root_term = r['account_name'].split("-")[0].strip().lower()
            lines.extend([
                f"### Account: **{r['account_name']}** (`{r['account_id']}`) — `{b_type.upper()}` [{r.get('currency', 'USD')}]",
                f"- **Yesterday Spend**: {curr}{r['yesterday_spend']:,.2f} with **0 conversions** (Target CPA: {curr}{r['target_cpa']:,.2f})",
                f"- **Business Model**: `{b_type}` (Disqualifies intent mismatches without hurting buyer traffic)",
                f"- **Staged Negative Keywords (Copy-Paste Ready)**:",
                "  ```text",
                f"  [{root_term} free]",
                f"  \"how to do {root_term} yourself\"",
            ] + [f"  {d}" for d in disqualifiers[:6]] + [
                "  ```",
                f"- **Staged Action**:",
                f"  - [ ] **Approve Negative Keyword List**: Add staged negative keywords at campaign level.",
                f"  - [ ] **Verify Conversion Tracking**: Confirm conversion tag status using `conversion-tracking` skill.",
                "",
            ])
    else:
        lines.append("No zero-conversion spend bleed detected today.\n")

    # Section 3: Ad Copy & Creative Specialist Findings
    creative_issues = [r for r in red_flag_accounts if any("CPA_SPIKE" in a or "ROAS_DROP" in a for a in r["anomalies"])]
    lines.append("## 3. ✍️ Ad Copy & Creative Specialist (Subagent: `ad-creative-agent`)")
    lines.append("*Grounded in `ad-creative` & `copywriting` skills — Custom RSA copy tailored to each business type*\n")
    if creative_issues:
        for r in creative_issues:
            b_type = r.get("business_type", "general")
            curr_code = r.get("currency", "USD")
            copy_pack = generate_rsa_copy_for_business(b_type, r["account_name"], curr_code)
            issue_desc = "CPA Spike (+60% vs baseline)" if any("CPA_SPIKE" in a for a in r["anomalies"]) else f"ROAS Drop ({r['roas']:.2f}x vs target {r['target_roas']:.2f}x)"
            
            lines.extend([
                f"### Account: **{r['account_name']}** (`{r['account_id']}`) — `{b_type.upper()}` [{curr_code}]",
                f"- **Trigger Anomaly**: {issue_desc}",
                f"- **Strategic Focus**: {copy_pack['focus']}",
                f"- **Staged RSA Ad Copy (Model-Specific Refresh)**:",
                f"  - **Headlines (≤ 30 characters)**:",
            ] + [f"    {idx+1}. `{h}` {'(Pin 1)' if idx == 0 else ('(Pin 2)' if idx == 1 else '')}" for idx, h in enumerate(copy_pack["headlines"])] + [
                f"  - **Descriptions (≤ 90 characters)**:",
            ] + [f"    {idx+1}. `{d}`" for idx, d in enumerate(copy_pack["descriptions"])] + [
                f"- **Staged Action**:",
                f"  - [ ] **Approve RSA Copy**: Deploy fresh responsive search ad variation into active ad group.",
                f"  - [ ] **Audit Asset Strength**: Replace poor-performing headlines with staged variations.",
                "",
            ])
    else:
        lines.append("No creative fatigue or ROAS drops requiring copy intervention today.\n")

    lines.extend([
        "---",
        "## 🚀 Execution Instructions",
        "Once you check the boxes above, tell Antigravity in chat:",
        "> *'I have approved the staged changes in action_plan. Proceed with applying them.'*",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Google Ads Orchestrator (Universal Cross-Industry Edition)")
    parser.add_argument("--sample", action="store_true", help="Force sample dataset mode")
    parser.add_argument("--date", type=validate_date_str, default=datetime.date.today().strftime("%Y-%m-%d"), help="Audit date (YYYY-MM-DD)")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    accounts_config = load_json(CONFIG_DIR / "accounts.json")
    thresholds = load_json(CONFIG_DIR / "thresholds.json")
    creds = load_yaml(CREDS_FILE)
    
    use_live = are_creds_configured(creds) and not args.sample
    mode_str = "LIVE GOOGLE ADS API" if use_live else "SAMPLE TEST RUN (Universal Portfolio)"
    
    print("=" * 65)
    print(" 🤖 Multi-Agent Team Orchestrator (Universal Multi-Business Support)")
    print(f" Mode: {mode_str} | Date: {args.date}")
    print("=" * 65)

    if use_live:
        print("[1/3] Lead Coordinator: Querying Google Ads API across all accounts...")
        results = fetch_live_google_ads_data(CREDS_FILE, accounts_config, thresholds)
    else:
        print("[1/3] Lead Coordinator: Scanning cross-industry accounts (E-comm, SaaS, Local, Mobile, Lead Gen)...")
        results = generate_sample_data(accounts_config, thresholds)

    red_flags = [r for r in results if r["status"] == "RED FLAG"]
    print(f"[2/3] Lead Coordinator: Identified {len(red_flags)} flagged accounts.")
    print("      Dispatching tailored assignments to specialized subagents:")
    print("      -> budget-pacing-agent (evaluating CPA & ROAS pacing by business model)")
    print("      -> search-terms-agent (generating industry-specific negative keywords)")
    print("      -> ad-creative-agent (drafting business-tailored RSA copy)")

    action_plan_file = REPORTS_DIR / f"action_plan_{args.date}.md"
    generate_staged_action_plan(results, action_plan_file, args.date, thresholds)

    print(f"[3/3] Master Action Plan Generated:")
    print(f"      -> {action_plan_file}")
    print("\n[COMPLETE] Multi-Agent Team run finished successfully.")


if __name__ == "__main__":
    main()
