export function sumModel(variables) {
  return {
    evaluate() {
      return variables.reduce((sum, v) => sum + v.sample(), 0);
    },
  };
}

/**
 * Net Present Value model: returns a timeline of cumulative NPV per year.
 * @param {{ initialInvestment: { sample(): number }, discountRate: { sample(): number }, cashflows: Array<{ sample(): number }> }} params
 * @returns {{ evaluate(): number[] }} Model that returns [npvYear0, npvYear1, ...]
 */
export function npvModel({ initialInvestment, discountRate, cashflows }) {
  return {
    evaluate() {
      const i = initialInvestment.sample();
      const r = discountRate.sample();
      const timeline = [-i];
      let npv = -i;
      for (let t = 1; t <= cashflows.length; t++) {
        const cf = cashflows[t - 1].sample();
        npv += cf / Math.pow(1 + r, t);
        timeline.push(npv);
      }
      return timeline;
    },
  };
}
