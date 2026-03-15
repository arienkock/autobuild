export function computeStats(results) {
  if (results.length === 0) {
    return {
      mean: 0,
      median: 0,
      stdDev: 0,
      band1Lower: 0,
      band1Upper: 0,
      band2Lower: 0,
      band2Upper: 0,
    };
  }
  const mean = results.reduce((a, b) => a + b, 0) / results.length;
  const sorted = [...results].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  const median =
    sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid];
  const variance =
    results.reduce((acc, x) => acc + (x - mean) ** 2, 0) / results.length;
  const stdDev = Math.sqrt(variance);
  return {
    mean,
    median,
    stdDev,
    band1Lower: mean - stdDev,
    band1Upper: mean + stdDev,
    band2Lower: mean - 2 * stdDev,
    band2Upper: mean + 2 * stdDev,
  };
}
