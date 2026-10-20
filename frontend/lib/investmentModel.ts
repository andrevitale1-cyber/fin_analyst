export type ModelMethod = "pe" | "normalized_pe" | "dcf" | "ev_ebitda" | "price_to_book";
export type ModelCase = {
  case: "bear" | "base" | "bull";
  assumptions: { rationale: string; source_ids: string[]; capacity_growth_percent: number; productivity_growth_percent: number;
    terminal_revenue_growth_percent: number; terminal_net_margin_percent: number; terminal_operating_margin_percent: number;
    capex_percent: number; depreciation_percent: number; incremental_working_capital_percent: number;
    tax_percent: number; discount_percent: number; equity_discount_percent: number; perpetual_growth_percent: number; terminal_pe: number; terminal_ev_ebitda: number; price_to_book: number };
  projections: { period: string; period_end: string; currency: string; revenue: number; net_income: number; eps: number | null; fcff: number;
    operating_income: number; ebitda: number; capex: number; source_ids: string[]; basis: "ai_assumption" }[];
  methods: { method: ModelMethod; present_value: number; future_value: number | null }[];
};
export type InvestmentModel = {
  version: string; available: boolean; selected_method: ModelMethod | null; fair_value: number | null; cross_check_methods: ModelMethod[];
  baseline: { period: string; valuation_date: string; currency: string; source_id: string; share_basis: string | null; shares: number | null; net_debt: number | null };
  assumptions: { profile: string; capacity_driver: string; productivity_driver: string; conviction: "low" | "medium" | "high"; rationale: string; counterthesis: string };
  cases: ModelCase[];
};
