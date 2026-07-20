"""Helpers for extracting annual financial facts from SEC companyfacts data."""

from datetime import date
from pathlib import Path


REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
]
OPERATING_INCOME_TAGS = ["OperatingIncomeLoss"]
NET_INCOME_TAGS = ["NetIncomeLoss"]
OPERATING_CASH_FLOW_TAGS = [
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
]
CAPEX_TAGS = ["PaymentsToAcquirePropertyPlantAndEquipment"]


def get_fact(facts, tag_candidates, unit="USD"):
    """Return annual values and the first matching tag from SEC companyfacts JSON.

    Values come from 10-K entries.  Duration facts must span 350--380 days;
    the latest filed entry for each end date is retained. Results are returned
    as ``(fiscal_year, value)`` pairs in ascending fiscal-year order. If no
    candidate tag exists, return
    ``(None, tag_candidates)``.
    """
    us_gaap = facts["facts"]["us-gaap"]

    for tag in tag_candidates:
        fact = us_gaap.get(tag)
        if fact is None:
            continue

        latest_by_end = {}
        for value in fact.get("units", {}).get(unit, []):
            if value.get("form") != "10-K" or not value.get("end"):
                continue

            start = value.get("start")
            if start:
                duration = (date.fromisoformat(value["end"]) - date.fromisoformat(start)).days
                if not 350 <= duration <= 380:
                    continue

            end = value["end"]
            if (
                end not in latest_by_end
                or value.get("filed", "") > latest_by_end[end].get("filed", "")
            ):
                latest_by_end[end] = value

        annual_values = [
            (int(end[:4]), value["val"])
            for end, value in sorted(latest_by_end.items())
        ]
        return annual_values, tag

    return None, tag_candidates


def build_metrics(ticker):
    """Build raw and derived annual financial metrics for *ticker*."""
    from edgar import get_companyfacts

    facts = get_companyfacts(ticker)
    candidates_by_metric = {
        "revenue": REVENUE_TAGS,
        "operating_income": OPERATING_INCOME_TAGS,
        "net_income": NET_INCOME_TAGS,
        "operating_cash_flow": OPERATING_CASH_FLOW_TAGS,
        "capex": CAPEX_TAGS,
    }
    raw = {}
    tags = {}
    for metric, candidates in candidates_by_metric.items():
        values, tag = get_fact(facts, candidates)
        raw[metric] = {} if values is None else dict(values)
        tags[metric] = tag

    years = sorted({year for series in raw.values() for year in series})

    def divide(numerator, denominator):
        if numerator is None or denominator in (None, 0):
            return None
        return numerator / denominator * 100

    derived = {
        "revenue_growth": {},
        "operating_margin": {},
        "free_cash_flow": {},
        "fcf_margin": {},
        "fcf_conversion": {},
    }
    for year in years:
        revenue = raw["revenue"].get(year)
        operating_income = raw["operating_income"].get(year)
        net_income = raw["net_income"].get(year)
        operating_cash_flow = raw["operating_cash_flow"].get(year)
        capex = raw["capex"].get(year)
        previous_revenue = raw["revenue"].get(year - 1)

        free_cash_flow = (
            operating_cash_flow - capex
            if operating_cash_flow is not None and capex is not None
            else None
        )
        derived["revenue_growth"][year] = divide(
            revenue - previous_revenue if revenue is not None and previous_revenue is not None else None,
            previous_revenue,
        )
        derived["operating_margin"][year] = divide(operating_income, revenue)
        derived["free_cash_flow"][year] = free_cash_flow
        derived["fcf_margin"][year] = divide(free_cash_flow, revenue)
        derived["fcf_conversion"][year] = divide(free_cash_flow, net_income)

    return {"ticker": ticker.upper(), "tags": tags, "raw": raw, "derived": derived}


def format_metrics_table(metrics):
    """Render raw and derived metrics as Markdown tables."""
    raw = metrics["raw"]
    derived = metrics["derived"]
    years = sorted({year for series in raw.values() for year in series})[-10:]

    def millions(value):
        return "—" if value is None else f"{value / 1_000_000:,.0f}"

    def percent(value):
        return "—" if value is None else f"{value:.1f}%"

    def render_table(headers, rows):
        rows = [row for row in rows if any(value != "—" for value in row[1:])]
        widths = [
            max(len(header), *(len(row[index]) for row in rows))
            for index, header in enumerate(headers)
        ]
        def render_row(row):
            return "| " + " | ".join(
                value.rjust(widths[index]) for index, value in enumerate(row)
            ) + " |"

        separator = "| " + " | ".join(
            "-" * max(3, width - 1) + ":" for width in widths
        ) + " |"
        return "\n".join([render_row(headers), separator, *(render_row(row) for row in rows)])

    raw_rows = []
    derived_rows = []
    for year in years:
        raw_rows.append(
            [
                str(year),
                *(millions(series.get(year)) for series in raw.values()),
            ]
        )
        derived_rows.append(
            [
                str(year),
                percent(derived["revenue_growth"].get(year)),
                percent(derived["operating_margin"].get(year)),
                millions(derived["free_cash_flow"].get(year)),
                percent(derived["fcf_margin"].get(year)),
                percent(derived["fcf_conversion"].get(year)),
            ]
        )

    raw_table = render_table(
        ["Year", "Revenue", "Operating income", "Net income", "Operating cash flow", "Capex"],
        raw_rows,
    )
    derived_table = render_table(
        ["Year", "Revenue growth", "Operating margin", "Free cash flow (millions)", "FCF margin", "FCF conversion"],
        derived_rows,
    )
    return raw_table + "\n\n" + derived_table


def write_report(ticker):
    """Save the Markdown metrics tables for *ticker* and return the report path."""
    report_path = Path("reports") / f"{ticker.upper()}_metrics.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(format_metrics_table(build_metrics(ticker)) + "\n", encoding="utf-8")
    return report_path


if __name__ == "__main__":
    print(format_metrics_table(build_metrics("AAPL")))
    write_report("AAPL")
