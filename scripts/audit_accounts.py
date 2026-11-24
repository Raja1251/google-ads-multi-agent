"""
Google Ads Multi-Account Auditor (Universal Cross-Industry Edition)
Supports all business types: E-Commerce, B2B SaaS, Local Services, Lead Gen, Mobile Apps, Info Products, Healthcare.
Queries Google Ads API via Manager Account (MCC) or runs with sample dataset.
Generates a timestamped CSV performance export and an executive Markdown brief.
"""

import os
import sys
import re
import json
import argparse
import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Paths relative to project root
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
REPORTS_DIR = BASE_DIR / "reports"
CREDS_FILE = BASE_DIR / "google-ads.yaml"

CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "AED": "AED ",
    "CAD": "CA$",
    "AUD": "A$",
    "SGD": "S$",
    "JPY": "¥",
}


def get_currency_symbol(curr_code: str) -> str:
    """Returns currency symbol for given ISO currency code."""
    if not curr_code:
        return "$"
    return CURRENCY_SYMBOLS.get(str(curr_code).upper(), f"{curr_code} ")


def validate_date_str(date_str: str) -> str:
    """Validates date string format strictly to prevent path traversal (YYYY-MM-DD)."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise argparse.ArgumentTypeError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")
    try:
        datetime.date.fromisoformat(date_str)
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid calendar date '{date_str}'.")


def load_json(filepath: Path) -> dict:
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(filepath: Path) -> dict:
    if not filepath.exists():
        return {}
    if yaml is not None:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    # Simple fallback parser for key: "value" YAML if PyYAML is not yet installed
    data = {}
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def are_creds_configured(creds: dict) -> bool:
    dev_token = creds.get("developer_token", "")
    client_id = creds.get("client_id", "")
    refresh_token = creds.get("refresh_token", "")
    if not dev_token or "INSERT_" in dev_token:
        return False
    if not client_id or "INSERT_" in client_id:
        return False
    if not refresh_token or "INSERT_" in refresh_token:
        return False
    return True


def generate_sample_data(accounts_config: dict, thresholds: dict) -> list:
    """Generates realistic sample metrics for 15 diverse cross-industry accounts."""
    import random
    random.seed(42)  # Deterministic test run
    
    accounts = accounts_config.get("accounts", [])
    results = []
    rules = thresholds.get("anomaly_rules", {})
    profiles = thresholds.get("business_type_profiles", {})
    
    cpa_spike_pct = rules.get("cpa_spike_percentage_vs_7d_avg", 25.0)
    budget_over_pct = rules.get("budget_pacing_overspend_threshold_pct", 15.0)
    budget_under_pct = rules.get("budget_pacing_underspend_threshold_pct", 30.0)
    roas_drop_target_pct = rules.get("roas_drop_percentage_vs_target", 25.0)
    default_cpa_mult = rules.get("zero_conversion_spend_cpa_multiplier", 1.5)
    default_min_zero_usd = rules.get("min_zero_conversion_spend_threshold_usd", 30.0)

    for i, acc in enumerate(accounts):
        cid = acc.get("id")
        name = acc.get("name")
        b_type = acc.get("business_type", "general")
        p_metric = acc.get("primary_metric", "CPA")
        target_cpa = float(acc.get("target_cpa", 50.0))
        target_roas = float(acc.get("target_roas")) if acc.get("target_roas") else None
        daily_budget = float(acc.get("daily_budget", 150.0))
        
        b_prof = profiles.get(b_type, {})
        cpa_mult = b_prof.get("zero_conversion_spend_cpa_multiplier", default_cpa_mult)
        zero_conv_limit = max(target_cpa * cpa_mult, default_min_zero_usd)
        
        # Introduce specific realistic anomalies mapped to different business types
        if i == 0:  # E-commerce ROAS Drop
            spend = daily_budget * 1.05
            conversions = 4
            roas = 1.95  # Target 3.8x -> severe ROAS drop
            baseline_cpa = target_cpa * 1.1
        elif i == 1:  # B2B SaaS: High CPA Spike
            spend = daily_budget * 1.10
            conversions = 1
            roas = 2.1
            baseline_cpa = target_cpa * 0.95
        elif i == 4:  # Lead Gen: Zero Conversion Spend Bleed
            spend = zero_conv_limit * 1.25
            conversions = 0
            roas = 0.0
            baseline_cpa = target_cpa
        elif i == 7:  # Healthcare: Budget Overrun
            spend = daily_budget * 1.35
            conversions = max(1, round(spend / target_cpa))
            roas = 3.2
            baseline_cpa = target_cpa
        elif i == 9:  # Local Service: Underpacing
            spend = daily_budget * 0.35
            conversions = max(1, round(spend / target_cpa))
            roas = 4.0
            baseline_cpa = target_cpa
        else:  # Healthy accounts
            spend = daily_budget * random.uniform(0.85, 1.05)
            conversions = max(1, round(spend / (target_cpa * random.uniform(0.85, 1.1))))
            roas = round((target_roas or 3.2) * random.uniform(0.95, 1.25), 2)
            baseline_cpa = target_cpa * random.uniform(0.9, 1.05)
            
        cpa = round(spend / conversions, 2) if conversions > 0 else 0.0
        impressions = round(spend * random.uniform(25, 45))
        clicks = round(impressions * random.uniform(0.02, 0.045))
        
        curr_code = acc.get("currency", "USD")
        curr_sym = get_currency_symbol(curr_code)

        # Evaluate anomaly rules
        anomalies = []
        if conversions == 0 and spend >= zero_conv_limit:
            anomalies.append(f"ZERO_CONV_BLEED ({curr_sym}{spend:.2f} spent with 0 conv; dynamic limit {curr_sym}{zero_conv_limit:.2f})")
            
        if conversions > 0 and baseline_cpa > 0:
            cpa_diff = ((cpa - baseline_cpa) / baseline_cpa) * 100
            if cpa_diff >= cpa_spike_pct:
                anomalies.append(f"CPA_SPIKE (+{cpa_diff:.1f}% vs 7D avg)")
                
        if p_metric == "ROAS" and target_roas and target_roas > 0:
            if roas < target_roas * (1 - roas_drop_target_pct / 100):
                drop_pct = ((target_roas - roas) / target_roas) * 100
                anomalies.append(f"ROAS_DROP ({roas:.2f}x vs target {target_roas:.2f}x, -{drop_pct:.1f}%)")
                
        if spend > daily_budget * (1 + budget_over_pct / 100):
            over_pct = ((spend - daily_budget) / daily_budget) * 100
            anomalies.append(f"BUDGET_OVERRUN (+{over_pct:.1f}% over daily budget)")
            
        if spend < daily_budget * (1 - budget_under_pct / 100):
            under_pct = ((daily_budget - spend) / daily_budget) * 100
            anomalies.append(f"UNDERPACING (-{under_pct:.1f}% under budget)")

        results.append({
            "account_id": cid,
            "account_name": name,
            "business_type": b_type,
            "primary_metric": p_metric,
            "yesterday_spend": round(spend, 2),
            "daily_budget": round(daily_budget, 2),
            "conversions": conversions,
            "cpa": cpa,
            "target_cpa": target_cpa,
            "baseline_7d_cpa": round(baseline_cpa, 2),
            "roas": roas,
            "target_roas": target_roas,
            "currency": curr_code,
            "clicks": clicks,
            "impressions": impressions,
            "anomalies": anomalies,
            "status": "RED FLAG" if anomalies else "HEALTHY"
        })
        
    return results


def fetch_live_google_ads_data(creds_path: Path, accounts_config: dict, thresholds: dict) -> list:
    """Queries live Google Ads API for all configured CIDs using GAQL."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
        from google.ads.googleads.errors import GoogleAdsException
    except ImportError:
        print("[ERROR] 'google-ads' package not installed. Run: pip install -r requirements.txt")
        sys.exit(1)

    client = GoogleAdsClient.load_from_storage(str(creds_path))
    ga_service = client.get_service("GoogleAdsService")
    
    accounts = accounts_config.get("accounts", [])
    results = []
    
    gaql_yesterday = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.status,
          metrics.cost_micros,
          metrics.impressions,
          metrics.clicks,
          metrics.conversions,
          metrics.cost_per_conversion,
          metrics.conversions_value
        FROM campaign
        WHERE segments.date DURING YESTERDAY
          AND campaign.status = 'ENABLED'
    """
    
    gaql_baseline = """
        SELECT
          metrics.cost_micros,
          metrics.conversions
        FROM customer
        WHERE segments.date DURING LAST_7_DAYS
    """
    
    rules = thresholds.get("anomaly_rules", {})
    profiles = thresholds.get("business_type_profiles", {})
    cpa_spike_pct = rules.get("cpa_spike_percentage_vs_7d_avg", 25.0)
    budget_over_pct = rules.get("budget_pacing_overspend_threshold_pct", 15.0)
    budget_under_pct = rules.get("budget_pacing_underspend_threshold_pct", 30.0)
    roas_drop_target_pct = rules.get("roas_drop_percentage_vs_target", 25.0)
    default_cpa_mult = rules.get("zero_conversion_spend_cpa_multiplier", 1.5)
    default_min_zero_usd = rules.get("min_zero_conversion_spend_threshold_usd", 30.0)

    for acc in accounts:
        cid = str(acc.get("id")).replace("-", "").strip()
        name = acc.get("name")
        b_type = acc.get("business_type", "general")
        p_metric = acc.get("primary_metric", "CPA")
        curr_code = acc.get("currency", "USD")
        curr_sym = get_currency_symbol(curr_code)
        target_cpa = float(acc.get("target_cpa", 50.0))
        target_roas = float(acc.get("target_roas")) if acc.get("target_roas") else None
        daily_budget = float(acc.get("daily_budget", 150.0))

        if not re.match(r"^\d{10}$", cid):
            print(f"    [WARNING] Invalid Customer ID format '{acc.get('id')}'. Skipping account.")
            continue
        
        b_prof = profiles.get(b_type, {})
        cpa_mult = b_prof.get("zero_conversion_spend_cpa_multiplier", default_cpa_mult)
        zero_conv_limit = max(target_cpa * cpa_mult, default_min_zero_usd)
        
        print(f"  -> Querying Account: {name} (CID: {cid}) [{b_type.upper()}]...")
        
        try:
            response = ga_service.search(customer_id=cid, query=gaql_yesterday)
            spend = 0.0
            conversions = 0.0
            conv_value = 0.0
            impressions = 0
            clicks = 0
            
            for row in response:
                spend += (row.metrics.cost_micros / 1_000_000.0)
                conversions += row.metrics.conversions
                conv_value += row.metrics.conversions_value
                impressions += row.metrics.impressions
                clicks += row.metrics.clicks
                
            cpa = (spend / conversions) if conversions > 0 else 0.0
            roas = (conv_value / spend) if spend > 0 else 0.0
            
            # 7-day baseline
            resp_base = ga_service.search(customer_id=cid, query=gaql_baseline)
            base_spend = 0.0
            base_conv = 0.0
            for r in resp_base:
                base_spend += (r.metrics.cost_micros / 1_000_000.0)
                base_conv += r.metrics.conversions
            
            baseline_7d_cpa = (base_spend / base_conv) if base_conv > 0 else target_cpa
            
            # Anomaly rules evaluation
            anomalies = []
            if conversions == 0 and spend >= zero_conv_limit:
                anomalies.append(f"ZERO_CONV_BLEED ({curr_sym}{spend:.2f} spent with 0 conv; dynamic limit {curr_sym}{zero_conv_limit:.2f})")
            if conversions > 0 and baseline_7d_cpa > 0:
                diff = ((cpa - baseline_7d_cpa) / baseline_7d_cpa) * 100
                if diff >= cpa_spike_pct:
                    anomalies.append(f"CPA_SPIKE (+{diff:.1f}% vs 7D avg)")
            if p_metric == "ROAS" and target_roas and target_roas > 0:
                if roas < target_roas * (1 - roas_drop_target_pct / 100):
                    drop_pct = ((target_roas - roas) / target_roas) * 100
                    anomalies.append(f"ROAS_DROP ({roas:.2f}x vs target {target_roas:.2f}x, -{drop_pct:.1f}%)")
            if spend > daily_budget * (1 + budget_over_pct / 100):
                over_pct = ((spend - daily_budget) / daily_budget) * 100
                anomalies.append(f"BUDGET_OVERRUN (+{over_pct:.1f}% over daily budget)")
            if spend < daily_budget * (1 - budget_under_pct / 100):
                under_pct = ((daily_budget - spend) / daily_budget) * 100
                anomalies.append(f"UNDERPACING (-{under_pct:.1f}% under budget)")

            results.append({
                "account_id": acc.get("id"),
                "account_name": name,
                "business_type": b_type,
                "primary_metric": p_metric,
                "yesterday_spend": round(spend, 2),
                "daily_budget": round(daily_budget, 2),
                "conversions": round(conversions, 1),
                "cpa": round(cpa, 2),
                "target_cpa": target_cpa,
                "baseline_7d_cpa": round(baseline_7d_cpa, 2),
                "roas": round(roas, 2),
                "target_roas": target_roas,
                "currency": curr_code,
                "clicks": clicks,
                "impressions": impressions,
                "anomalies": anomalies,
                "status": "RED FLAG" if anomalies else "HEALTHY"
            })

        except GoogleAdsException as ex:
            print(f"    [WARNING] Error querying CID {cid}: {ex.error.message}")
            results.append({
                "account_id": acc.get("id"),
                "account_name": name,
                "business_type": b_type,
                "primary_metric": p_metric,
                "yesterday_spend": 0.0,
                "daily_budget": daily_budget,
                "conversions": 0,
                "cpa": 0.0,
                "target_cpa": target_cpa,
                "baseline_7d_cpa": 0.0,
                "roas": 0.0,
                "target_roas": target_roas,
                "clicks": 0,
                "impressions": 0,
                "anomalies": [f"API_ERROR: {ex.error.code().name}"],
                "status": "ERROR"
            })
            
    return results


def export_csv(results: list, output_path: Path):
    resolved = output_path.resolve()
    if not resolved.is_relative_to(REPORTS_DIR.resolve()):
        raise ValueError(f"Security violation: path traversal detected for {resolved}")
    import csv
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Account_ID", "Account_Name", "Business_Type", "Primary_Metric", "Currency", "Status",
            "Yesterday_Spend", "Daily_Budget", "Conversions", "CPA", "Target_CPA",
            "ROAS", "Target_ROAS", "7D_Avg_CPA", "Clicks", "Impressions", "Anomalies"
        ])
        for r in results:
            target_roas_str = f"{r['target_roas']:.2f}x" if r.get("target_roas") else "N/A"
            curr_sym = get_currency_symbol(r.get("currency", "USD"))
            writer.writerow([
                r["account_id"],
                r["account_name"],
                r.get("business_type", "general"),
                r.get("primary_metric", "CPA"),
                r.get("currency", "USD"),
                r["status"],
                f"{curr_sym}{r['yesterday_spend']:,.2f}",
                f"{curr_sym}{r['daily_budget']:,.2f}",
                r["conversions"],
                f"{curr_sym}{r['cpa']:,.2f}",
                f"{curr_sym}{r['target_cpa']:,.2f}",
                f"{r['roas']:.2f}x",
                target_roas_str,
                f"{curr_sym}{r['baseline_7d_cpa']:,.2f}",
                r["clicks"],
                r["impressions"],
                " | ".join(r["anomalies"]) if r["anomalies"] else "None"
            ])


def export_markdown_summary(results: list, output_path: Path, date_str: str, mode: str):
    resolved = output_path.resolve()
    if not resolved.is_relative_to(REPORTS_DIR.resolve()):
        raise ValueError(f"Security violation: path traversal detected for {resolved}")
    
    total_spend = sum(r["yesterday_spend"] for r in results)
    total_conv = sum(r["conversions"] for r in results)
    overall_cpa = (total_spend / total_conv) if total_conv > 0 else 0.0
    red_flag_accounts = [r for r in results if r["status"] == "RED FLAG"]
    error_accounts = [r for r in results if r["status"] == "ERROR"]

    md_lines = [
        f"# Google Ads Multi-Account Executive Audit - {date_str}",
        f"\n**Execution Mode**: `{mode}` | **Audited Accounts**: {len(results)} accounts (Universal Cross-Industry & Multi-Currency)\n",
        "## Key Performance Summary",
        f"- **Total Portfolio Conversions**: `{total_conv:,.1f}`",
        f"- **Accounts Requiring Attention**: `{len(red_flag_accounts)}` red flags, `{len(error_accounts)}` errors\n",
    ]

    if red_flag_accounts:
        md_lines.append("## 🚨 Immediate Action Required (Red Flags)")
        md_lines.append("| Account ID | Account Name | Model | Curr | Spend | Conv | Target Metric | Anomaly Detected |")
        md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in red_flag_accounts:
            flags = "<br>".join([f"⚠️ {a}" for a in r["anomalies"]])
            curr_sym = get_currency_symbol(r.get("currency", "USD"))
            target_str = f"ROAS: {r['roas']:.2f}x (Target {r['target_roas']:.2f}x)" if r.get("primary_metric") == "ROAS" else f"CPA: {curr_sym}{r['cpa']:,.2f} (Target {curr_sym}{r['target_cpa']:,.2f})"
            md_lines.append(
                f"| `{r['account_id']}` | **{r['account_name']}** | `{r.get('business_type', 'general')}` | `{r.get('currency', 'USD')}` | {curr_sym}{r['yesterday_spend']:,.2f} | {r['conversions']} | {target_str} | {flags} |"
            )
        md_lines.append("")

    md_lines.append("## 📊 Full Portfolio Breakdown")
    md_lines.append("| Account | Model | Curr | Status | Spend / Budget | Conv | CPA | ROAS | Primary Goal |")
    md_lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        status_badge = "🔴 Red Flag" if r["status"] == "RED FLAG" else ("🟢 Healthy" if r["status"] == "HEALTHY" else "⚠️ Error")
        curr_sym = get_currency_symbol(r.get("currency", "USD"))
        goal_str = f"Target ROAS: {r['target_roas']:.2f}x" if r.get("primary_metric") == "ROAS" else f"Target CPA: {curr_sym}{r['target_cpa']:,.2f}"
        md_lines.append(
            f"| **{r['account_name']}** (`{r['account_id']}`) | `{r.get('business_type', 'general')}` | `{r.get('currency', 'USD')}` | {status_badge} | {curr_sym}{r['yesterday_spend']:,.2f} / {curr_sym}{r['daily_budget']:,.2f} | {r['conversions']} | {curr_sym}{r['cpa']:,.2f} | {r['roas']:.2f}x | {goal_str} |"
        )

    md_lines.append("\n## 💡 Tailored Marketing Recommendations by Business Type")
    md_lines.append("1. **E-Commerce & Retail**: Protect Target ROAS and cart efficiency. For `ROAS_DROP`, audit product-level margin tiers in Performance Max and exclude non-converting search terms.")
    md_lines.append("2. **B2B SaaS**: Focus on demo and pipeline quality. For `CPA_SPIKE`, refresh RSA copy with verified proof points and exclude non-buyer intents (`jobs`, `salary`, `crack`).")
    md_lines.append("3. **Local & Emergency Services**: Optimize for high-intent call actions and radius boundaries. Ensure negative lists filter out distant locations and DIY repairs.")
    md_lines.append("4. **Lead Generation**: Verify form validation and CRM offline conversion tracking to prevent spend bleed on uncontacted leads.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


def main():
    parser = argparse.ArgumentParser(description="Multi-Account Google Ads Auditor")
    parser.add_argument("--sample", action="store_true", help="Force sample dataset mode")
    parser.add_argument("--date", type=validate_date_str, default=datetime.date.today().strftime("%Y-%m-%d"), help="Audit date (YYYY-MM-DD)")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    accounts_config = load_json(CONFIG_DIR / "accounts.json")
    thresholds = load_json(CONFIG_DIR / "thresholds.json")
    creds = load_yaml(CREDS_FILE)
    
    use_live = are_creds_configured(creds) and not args.sample
    mode_str = "LIVE GOOGLE ADS API" if use_live else "SAMPLE TEST RUN (Pending live credentials in google-ads.yaml)"
    
    print(f"==================================================")
    print(f" Google Ads Universal Multi-Account Auditor")
    print(f" Mode: {mode_str}")
    print(f" Date: {args.date}")
    print(f"==================================================")

    if use_live:
        print("[INFO] Authenticating with Google Ads API (MCC)...")
        results = fetch_live_google_ads_data(CREDS_FILE, accounts_config, thresholds)
    else:
        if not args.sample:
            print("[NOTICE] Placeholder values found in 'google-ads.yaml'.")
            print("         Running in SAMPLE MODE across diverse business models.")
            print("         Insert your live credentials into 'google-ads.yaml' to connect live.\n")
        results = generate_sample_data(accounts_config, thresholds)

    # Export outputs
    csv_file = REPORTS_DIR / f"audit_{args.date}.csv"
    md_file = REPORTS_DIR / f"summary_{args.date}.md"
    
    export_csv(results, csv_file)
    export_markdown_summary(results, md_file, args.date, mode_str)

    print(f"\n[SUCCESS] Universal Audit Complete!")
    print(f"  -> CSV Export: {csv_file}")
    print(f"  -> Markdown Summary: {md_file}")
    
    red_flags = [r for r in results if r["status"] == "RED FLAG"]
    if red_flags:
        print(f"\n[ALERT] Found {len(red_flags)} accounts with anomalies requiring attention!")
    else:
        print(f"\n[OK] All accounts healthy.")


if __name__ == "__main__":
    main()
