/**
 * NPV (Net Present Value) model: timeline of value over years for break-even analysis.
 * Public API: createNPVModel(spec) → { resultShape: 'timeline', run(random) }.
 */

import { RESULT_SHAPE } from './model.js';
import { sample } from './variable.js';

/**
 * Resolve a spec value: if it's a number return it, else sample the variable.
 * @param {number | { type: string, [key: string]: unknown }} valueOrVar
 * @param {() => number} random
 * @returns {number}
 */
function resolveValue(valueOrVar, random) {
  if (typeof valueOrVar === 'number') return valueOrVar;
  return sample(valueOrVar, random);
}

/**
 * Build NPV timeline for one run: [npv_year0, npv_year1, ..., npv_yearN].
 * npv_year0 = -initialInvestment; npv_yearT = -initial + sum(cf_i / (1+r)^i) for i=1..T.
 *
 * @param {number} initialInvestment
 * @param {number} discountRate - decimal (e.g. 0.1 for 10%)
 * @param {number[]} cashflowSamples - length = years, cashflow for year 1, 2, ... years
 * @returns {number[]}
 */
export function computeNPVTimeline(initialInvestment, discountRate, cashflowSamples) {
  const timeline = [-initialInvestment];
  let pv = -initialInvestment;
  for (let t = 0; t < cashflowSamples.length; t++) {
    const cf = cashflowSamples[t];
    const factor = Math.pow(1 + discountRate, -(t + 1));
    pv += cf * factor;
    timeline.push(pv);
  }
  return timeline;
}

/**
 * @param {{ initialInvestment: number | import('./variable.js').Variable, cashflows: (number | import('./variable.js').Variable)[] | (number | import('./variable.js').Variable), discountRate: number | import('./variable.js').Variable, years: number }} spec
 * @returns {{ resultShape: 'timeline', run: (random?: () => number) => number[] }}
 */
export function createNPVModel(spec) {
  const { initialInvestment, cashflows, discountRate, years } = spec;
  const isArrayCF = Array.isArray(cashflows);

  return {
    resultShape: RESULT_SHAPE.TIMELINE,
    run(random = Math.random) {
      const initial = resolveValue(initialInvestment, random);
      const rate = resolveValue(discountRate, random);
      const cfSamples = [];
      for (let t = 0; t < years; t++) {
        const cf = isArrayCF ? resolveValue(cashflows[t], random) : resolveValue(cashflows, random);
        cfSamples.push(cf);
      }
      return computeNPVTimeline(initial, rate, cfSamples);
    },
  };
}
