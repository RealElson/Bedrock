"""Flatten build_metrics output into the field names stages declare in `requires`.

The stage frontmatter declares flat names (fcf_series, coverage_ratio, mdna_text).
build_metrics returns nested raw/derived dicts. This module is the contract between
them. Anything genuinely absent from the filings is returned as None so the runner
skips that stage honestly rather than fabricating a value.
"""

import edgar
from compute import build_metrics, get_fact

# Gross debt is not a single XBRL tag. Sum whichever of these exist.
DEBT_TAGS = [
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "CommercialPaper",
    "OtherShortTermBorrowings",
]


def _year_key(series, year):
    """Look up a year whether the dict is keyed by int or str."""
    if year in series:
        return series[year]
    if str(year) in series:
        return series[str(year)]
    return None


def _latest(series):
    """Return (year, value) for the most recent year in a {year: value} dict."""
    if not series:
        return None, None
    key = max(series, key=lambda y: int(y))
    return int(key), series[key]


def _get_debt(facts):
    """Sum available debt tags for the most recent fiscal year."""
    total = 0
    found = []
    for tag in DEBT_TAGS:
        try:
            values, matched_tag = get_fact(facts, [tag])
        except Exception:
            continue
        if not values:
            continue
        # get_fact returns a list of (year, value) tuples, ascending.
        year, value = values[-1]
        if value:
            total += value
            found.append(f"{matched_tag or tag}:{year}")
    return (total, found) if found else (None, [])


def build_stage_inputs(ticker):
    """Return a flat dict keyed by the names stages declare in `requires`."""
    metrics = build_metrics(ticker)
    raw = metrics["raw"]

    revenue = raw.get("revenue", {})
    operating_income = raw.get("operating_income", {})
    net_income = raw.get("net_income", {})
    ocf = raw.get("operating_cash_flow", {})
    capex = raw.get("capex", {})

    # Free cash flow for every year where both inputs exist.
    fcf_series = {
        year: ocf[year] - capex[year]
        for year in ocf
        if year in capex
    }

    latest_year, latest_revenue = _latest(revenue)
    _, latest_op_income = _latest(operating_income)
    _, latest_net_income = _latest(net_income)
    _, latest_fcf = _latest(fcf_series)

    reported_revenue_change = None
    if latest_year:
        prior = _year_key(revenue, latest_year - 1)
        if prior and latest_revenue:
            reported_revenue_change = round(
                (latest_revenue - prior) / prior * 100, 2
            )

    statutory_margin = None
    if latest_revenue and latest_op_income:
        statutory_margin = round(latest_op_income / latest_revenue * 100, 2)

    facts = edgar.get_companyfacts(ticker)
    gross_debt, debt_tags_used = _get_debt(facts)
    coverage_ratio = None
    if gross_debt and latest_op_income:
        coverage_ratio = round(gross_debt / latest_op_income, 2)

    # MD&A text. Non-fatal if the fetch fails.
    mdna_text = None
    try:
        mdna_text = edgar.extract_item(
            edgar.get_10k_text(ticker), "Item 7.", "Item 7A."
        )
    except Exception:
        pass

    return {
        # --- Stage 2 ---
        "mdna_text": mdna_text,
        # --- Stage 2.5 ---
        "annual_earnings_series": net_income,
        "current_period_earnings": latest_net_income,
        # one-time items are not machine-extractable from XBRL. Left as None so
        # the stage is skipped rather than assuming no adjustments exist.
        "one_time_items": None,
        # --- Stage 3 ---
        "reported_revenue_change": reported_revenue_change,
        "statutory_margin": statutory_margin,
        # Apple does not report constant-currency or acquisition contribution.
        # These stay None; Stage 3 skipping is the correct outcome, not a bug.
        "fx_impact": None,
        "ma_contribution": None,
        "underlying_margin": None,
        # --- Stage 6 ---
        "gross_debt": gross_debt,
        "underlying_operating_profit": latest_op_income,
        "coverage_ratio": coverage_ratio,
        # --- Stage 13 ---
        "revenue": revenue,
        "net_income": net_income,
        "operating_cash_flow": ocf,
        "capex": capex,
        "fcf_series": fcf_series,
        # --- context passed to every stage ---
        "_meta": {
            "ticker": ticker.upper(),
            "latest_fiscal_year": latest_year,
            "latest_fcf": latest_fcf,
            "debt_tags_used": debt_tags_used,
            "tags": metrics.get("tags", {}),
        },
    }


if __name__ == "__main__":
    inputs = build_stage_inputs("AAPL")
    for key, value in inputs.items():
        if key == "mdna_text":
            print(f"{key}: {len(value) if value else 0} chars")
        elif key == "_meta":
            print(f"{key}: {value}")
        elif isinstance(value, dict):
            print(f"{key}: {len(value)} years")
        else:
            print(f"{key}: {value}")
