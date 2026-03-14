/**
 * NPV model: evaluates to a timeline of cumulative net present value over years.
 * Each evaluation returns an array [npv0, npv1, ..., npvYears] so the break-even
 * point can be identified along the timeline.
 *
 * Variables: [discountRateVariable, cashflowVariable]
 * - discountRateVariable: sampled once per iteration (e.g. 0.05 for 5%)
 * - cashflowVariable: sampled once per year (uncertainty per period)
 *
 * Config: { initialInvestment: number, years: number }
 */
function npvEvaluator(initialInvestment, years) {
  return function (variables) {
    const [rateVar, cashflowVar] = variables;
    const r = rateVar.sample();
    const timeline = [-initialInvestment];
    let npv = -initialInvestment;
    for (let t = 1; t <= years; t++) {
      const cf = cashflowVar.sample();
      npv += cf / Math.pow(1 + r, t);
      timeline.push(npv);
    }
    return timeline;
  };
}

export { npvEvaluator };
