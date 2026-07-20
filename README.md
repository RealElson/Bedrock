# Metric-style Practice Contract

This is a **training artifact**, not a real protocol. It's modeled loosely on what's
publicly known about Metric (an upcoming Sherlock contest): a DEX that prices swaps
entirely from external oracle feeds rather than an onchain reserves-based curve
("active pool standard").

It is **not** a copy of Metric's actual code — Metric's real repo isn't public yet.
This is a from-scratch contract built to be structurally similar in spirit
(oracle-priced pool, deposit/withdraw shares, swap logic) so you have something live
to run your checklist against before the real contest opens Monday.

## Structure

```
contracts/
  ActivePool.sol            <- main audit target
  oracle/
    IPriceOracle.sol         <- oracle interface (Chainlink-style, 1e8 precision)
    MockPriceOracle.sol      <- test oracle, lets you set price/updatedAt/confidence manually
  tokens/
    LPToken.sol              <- bare-bones share token (scaffolding, not the target)
```

## How to use this

Treat `ActivePool.sol` as if it just dropped into a live contest. Don't read this
README's hints below until after your first pass — the point is to exercise your own
instincts cold.

Suggested approach:
1. Read `ActivePool.sol` top to bottom once, no tools, like you always do.
2. Run your five-question checklist against it (accrual/state ordering, position
   health after state changes, oracle validation, global tracker correctness, admin
   function impact on existing users) — plus your oracle-specific checks (staleness,
   confidence interval, zero price, decimals/precision).
3. Write Forge tests that try to prove out anything suspicious.
4. Only then, come back here and we'll compare notes on what you found vs. what's
   actually in there.

## Setting up Foundry

```bash
cd metric-practice
forge init --no-commit --force
# copy contracts/ into src/ per your foundry.toml layout, or adjust remappings
```

`MockPriceOracle` lets you simulate: stale prices, zero prices, wide confidence
intervals (field is returned but not necessarily *used* everywhere it should be —
worth checking), and independent staleness per asset.

## Scope note

This contract intentionally has **more than one** finding in it, across more than one
severity. Some are the kind of thing that would be Critical/High in a real contest,
some are lower severity or just bad practice. Find what you can before asking me.
