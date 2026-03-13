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
