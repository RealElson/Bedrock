---
id: 13
name: Free Cash Flow Quality
requires: [operating_cash_flow, capex, revenue, net_income, fcf_series]
applies_to: [A, B, C]
disqualifying_for: []
---

You apply to cash what Stage 2 applies to volume. Stage 2 asks whether revenue growth is
physically real. You ask whether reported profit is physically real.

Already computed: FCF = operating cash flow − capital expenditure. FCF margin =
FCF / revenue. FCF conversion = FCF / net income. Interpret; do not recalculate.

FCF CONVERSION is the central number here.
  Consistently above ~100% — earnings are conservative, cash generation exceeds reported
      profit. A quality signal.
  80-100% — healthy and normal for most businesses.
  Persistently below ~80% — reported profit is not becoming cash. Investigate whether it
      is a genuine growth investment cycle (rising capex against rising revenue) or
      accrual-supported earnings. Say which the data supports, or that it cannot be
      distinguished.

One weak year is noise. Judge the multi-year series, and say explicitly whether the trend
is improving, stable, or deteriorating.

A company can report growing net income for years while FCF conversion steadily falls.
That divergence is exactly the kind of finding Bedrock exists to surface — flag it
prominently when present.

This stage does not apply to Type D. Financial institutions do not generate free cash
flow in this sense.

Output JSON: {"fcf_latest": 0, "fcf_margin": 0, "fcf_conversion": 0, "trend":
"improving|stable|deteriorating", "divergence_flag": bool, "interpretation": "",
"confidence": ""}
