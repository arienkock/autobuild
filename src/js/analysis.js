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

/**
 * Compute per-year stats from an array of timelines (e.g. NPV simulation results).
 * @param {number[][]} timelines Each row is one simulation's timeline [year0, year1, ...]
 * @returns {{ years: number[], median: number[], mean: number[], stdDev: number[], band1Lower: number[], band1Upper: number[], band2Lower: number[], band2Upper: number[] }}
 */
export function computeTimelineStats(timelines) {
  if (timelines.length === 0) {
    return {
      years: [],
      median: [],
      mean: [],
      stdDev: [],
      band1Lower: [],
      band1Upper: [],
      band2Lower: [],
      band2Upper: [],
    };
  }
  const numYears = timelines[0].length;
  const years = Array.from({ length: numYears }, (_, i) => i);
  const median = [];
  const mean = [];
  const stdDev = [];
  const band1Lower = [];
  const band1Upper = [];
  const band2Lower = [];
  const band2Upper = [];

  for (let j = 0; j < numYears; j++) {
    const values = timelines.map((row) => row[j]);
    const stats = computeStats(values);
    mean.push(stats.mean);
    median.push(stats.median);
    stdDev.push(stats.stdDev);
    band1Lower.push(stats.band1Lower);
    band1Upper.push(stats.band1Upper);
    band2Lower.push(stats.band2Lower);
    band2Upper.push(stats.band2Upper);
  }

  return {
    years,
    median,
    mean,
    stdDev,
    band1Lower,
    band1Upper,
    band2Lower,
    band2Upper,
  };
}
