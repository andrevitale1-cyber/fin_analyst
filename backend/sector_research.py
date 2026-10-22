"""Issuer-specific research requirements shared by extraction, writing and review."""

VERSION = "petrobras-research-v1"


def is_petrobras(company):
    return company.upper() in {"PETR3", "PETR4", "PBR", "PBR.A"}


def sector_brief(company):
    if not is_petrobras(company):
        return ""
    return """PETROBRAS — INTEGRATED OIL AND GAS, STATE-CONTROLLED ISSUER.
Research the company across the commodity cycle, not as a generic growth company.
Obtain original annual consolidated statements for the latest five full years and latest interim results,
production reports, current business plan, dividend policy and the latest earnings call/Q&A.
Read original tables, including 2025 annual results when available as of the research date.
Separate E&P, refining/transport/marketing, gas/power and corporate/intersegment eliminations.
Collect oil/gas production and sales (not interchangeable), pre-salt mix, lifting costs with/without government
take, Brent and realized oil prices, refinery utilization, refining margins, reserves/replacement, platform
startups and decline rates. Explain why upstream and refining revenue cannot simply be added before eliminations.
Collect capex by activity, maintenance versus expansion when disclosed, operating cash, debt INCLUDING lease
obligations, cash, noncontrolling interests, outstanding ON+PN shares and economic rights of PETR3/PETR4.
Keep BRL underlying shares separate from USD ADRs; no upside comparison across those bases.
Explain price policy and import/export parity, shareholder control, governance protections and interference
channels, project economics, capital allocation and dividend coverage from recurring cash after investment.
Separate ordinary distributions, extraordinary dividends, JCP, accounting FX effects and recurring earnings.
Use the current business plan as management guidance, not guaranteed production or analyst consensus.
Each section must link evidence to economic consequences and falsifiable thesis conditions. Discuss why an
integrated asset base can be strong while commodity exposure and state control still require a discount.
Valuation must use explicit five-year operating/cash-flow assumptions, Brent, USD/BRL, production,
segment EBITDA, depreciation, capex, working capital and taxes; DCF first, EV/EBITDA cross-check.
Justify WACC, terminal reinvestment/reserve replacement and comparable-company adjustments. Do not value
finite reserves by growing cash forever without the reinvestment needed to sustain production.
Dividends are a consequence of distributable cash and policy, not a perpetual yield extrapolation.
Show bear/base/bull drivers and downside mechanisms; never force a target price or use a guessed P/E on
one historical EPS. Missing critical evidence blocks editorial publication rather than becoming filler."""
