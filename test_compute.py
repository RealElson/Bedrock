"""Regression checks for annual facts reported in Apple's FY2025 10-K."""

from compute import (
    CAPEX_TAGS,
    NET_INCOME_TAGS,
    OPERATING_CASH_FLOW_TAGS,
    OPERATING_INCOME_TAGS,
    REVENUE_TAGS,
    get_fact,
)
from edgar import get_companyfacts


MILLION = 1_000_000


def values_in_millions(facts, candidates):
    values, _ = get_fact(facts, candidates)
    return [(fiscal_year, value // MILLION) for fiscal_year, value in values]


facts = get_companyfacts("AAPL")

assert values_in_millions(facts, REVENUE_TAGS)[-5:] == [
    (2021, 365817),
    (2022, 394328),
    (2023, 383285),
    (2024, 391035),
    (2025, 416161),
]
assert values_in_millions(facts, OPERATING_CASH_FLOW_TAGS)[-5:] == [
    (2021, 104038),
    (2022, 122151),
    (2023, 110543),
    (2024, 118254),
    (2025, 111482),
]
assert values_in_millions(facts, OPERATING_INCOME_TAGS)[-3:] == [
    (2023, 114301),
    (2024, 123216),
    (2025, 133050),
]
assert values_in_millions(facts, NET_INCOME_TAGS)[-3:] == [
    (2023, 96995),
    (2024, 93736),
    (2025, 112010),
]
assert values_in_millions(facts, CAPEX_TAGS)[-3:] == [
    (2023, 10959),
    (2024, 9447),
    (2025, 12715),
]
