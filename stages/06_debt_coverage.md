---
id: 6
name: Debt Coverage — Graham Safety Layer
requires: [gross_debt, underlying_operating_profit, coverage_ratio]
applies_to: [A, B, C]
disqualifying_for: []
---

Measure balance sheet safety by the company's ability to clear obligations from real
earnings, not by arbitrary debt levels.

Coverage = Gross Debt / Underlying Operating Profit. Already computed.

  ≤ 3.0x for a predictable business — extraordinarily safe
  > 4.0x — warrants caution
  > 5.0x — risk flag

Quantify before fearing. A manageable load on a high-margin business is not a crisis;
say so when that is what the number shows. Note that this stage does not apply to Type D
— leverage is the business model at a financial institution, not a risk signal.

Output JSON: {"coverage_ratio": 0, "band": "safe|caution|risk", "interpretation": "",
"passed": bool}
