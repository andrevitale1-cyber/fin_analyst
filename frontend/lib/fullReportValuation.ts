export type ValuationInputs = { growthPercent: number; peMultiple: number; discountPercent: number };

export function calculateIllustrativeValue(annualEps: number, inputs: ValuationInputs): number | null {
  const { growthPercent, peMultiple, discountPercent } = inputs;
  if (!Number.isFinite(annualEps) || annualEps <= 0 ||
      !Number.isFinite(growthPercent) || growthPercent < -50 || growthPercent > 100 ||
      !Number.isFinite(peMultiple) || peMultiple < 1 || peMultiple > 100 ||
      !Number.isFinite(discountPercent) || discountPercent < 0 || discountPercent > 50) return null;

  const growth = growthPercent / 100;
  const discount = discountPercent / 100;
  const value = annualEps * (1 + growth) ** 5 * peMultiple / (1 + discount) ** 5;
  return Number.isFinite(value) && value > 0 ? value : null;
}
