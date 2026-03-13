export function mean(values) {
  if (values.length === 0) return NaN;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

export function median(values) {
  if (values.length === 0) return NaN;
  const sorted = [...values].sort((a, b) => a - b);
  const m = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[m - 1] + sorted[m]) / 2;
  }
  return sorted[m];
}

export function stdDev(values) {
  if (values.length < 2) return 0;
  const m = mean(values);
  const variance =
    values.reduce((acc, x) => acc + (x - m) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
}

export function summary(values) {
  const m = mean(values);
  const med = median(values);
  const sd = stdDev(values);
  return {
    mean: m,
    median: med,
    stdDev: sd,
    minus2Sigma: m - 2 * sd,
    minus1Sigma: m - sd,
    plus1Sigma: m + sd,
    plus2Sigma: m + 2 * sd,
  };
}

/**
 * Per-year summary across many timeline runs (e.g. NPV over years).
 * @param {number[][]} timelines - each row is one run: [value_year0, value_year1, ...]
 * @returns {{ yearCount: number, median: number[], minus2Sigma: number[], minus1Sigma: number[], plus1Sigma: number[], plus2Sigma: number[] }}
 */
export function timelineSummary(timelines) {
  if (timelines.length === 0) {
    return { yearCount: 0, median: [], minus2Sigma: [], minus1Sigma: [], plus1Sigma: [], plus2Sigma: [] };
  }
  const yearCount = timelines[0].length;
  const medians = [];
  const minus2Sigma = [];
  const minus1Sigma = [];
  const plus1Sigma = [];
  const plus2Sigma = [];
  for (let t = 0; t < yearCount; t++) {
    const values = timelines.map((row) => row[t]);
    const m = mean(values);
    const med = median(values);
    const sd = stdDev(values);
    medians.push(med);
    minus2Sigma.push(m - 2 * sd);
    minus1Sigma.push(m - sd);
    plus1Sigma.push(m + sd);
    plus2Sigma.push(m + 2 * sd);
  }
  return { yearCount, median: medians, minus2Sigma, minus1Sigma, plus1Sigma, plus2Sigma };
}
