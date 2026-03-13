import { npv } from "./npv.js";
import { randomNormalWith } from "./random.js";

function sortNumbers(values) {
  const copy = values.slice();
  copy.sort((a, b) => a - b);
  return copy;
}

function quantile(sorted, p) {
  if (sorted.length === 0) {
    return NaN;
  }
  const index = (sorted.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) {
    return sorted[lower];
  }
  const w = index - lower;
  return sorted[lower] * (1 - w) + sorted[upper] * w;
}

export function runMonteCarlo(params) {
  const {
    initialInvestment,
    annualCashFlowMean,
    annualCashFlowStdDev,
    years,
    discountRate,
    iterations,
  } = params;

  if (!Number.isFinite(initialInvestment)) {
    throw new TypeError("initialInvestment must be finite");
  }
  if (!Number.isFinite(annualCashFlowMean)) {
    throw new TypeError("annualCashFlowMean must be finite");
  }
  if (!Number.isFinite(annualCashFlowStdDev) || annualCashFlowStdDev < 0) {
    throw new TypeError("annualCashFlowStdDev must be a non-negative finite number");
  }
  if (!Number.isInteger(years) || years <= 0) {
    throw new TypeError("years must be a positive integer");
  }
  if (!Number.isFinite(discountRate)) {
    throw new TypeError("discountRate must be finite");
  }
  if (!Number.isInteger(iterations) || iterations <= 0) {
    throw new TypeError("iterations must be a positive integer");
  }

  const npvs = [];
  let sum = 0;
  let sumSq = 0;
  let positiveCount = 0;

  for (let i = 0; i < iterations; i += 1) {
    const cashFlows = [initialInvestment];
    for (let t = 0; t < years; t += 1) {
      const cf = randomNormalWith(annualCashFlowMean, annualCashFlowStdDev);
      cashFlows.push(cf);
    }
    const value = npv(cashFlows, discountRate);
    npvs.push(value);
    sum += value;
    sumSq += value * value;
    if (value > 0) {
      positiveCount += 1;
    }
  }

  const meanNpv = sum / iterations;
  const variance = iterations > 1 ? (sumSq - (sum * sum) / iterations) / (iterations - 1) : 0;
  const stdNpv = Math.sqrt(Math.max(0, variance));
  const probPositive = positiveCount / iterations;

  const sorted = sortNumbers(npvs);

  return {
    meanNpv,
    stdNpv,
    probPositive,
    p5: quantile(sorted, 0.05),
    p50: quantile(sorted, 0.5),
    p95: quantile(sorted, 0.95),
  };
}
