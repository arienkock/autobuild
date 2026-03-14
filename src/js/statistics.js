function mean(arr) {
  if (arr.length === 0) return NaN;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function median(arr) {
  if (arr.length === 0) return NaN;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function stdDev(arr) {
  if (arr.length < 2) return 0;
  const m = mean(arr);
  const squaredDiffs = arr.map((x) => Math.pow(x - m, 2));
  return Math.sqrt(squaredDiffs.reduce((a, b) => a + b, 0) / arr.length);
}

function getSummary(results) {
  const m = mean(results);
  const sd = stdDev(results);
  return {
    mean: m,
    median: median(results),
    stdDev: sd,
    minus2StdDev: m - 2 * sd,
    minus1StdDev: m - sd,
    plus1StdDev: m + sd,
    plus2StdDev: m + 2 * sd,
  };
}

/**
 * For timeline results (array of arrays). For each time index, compute
 * median and sigma bands across all iterations. Returns bands for 50th percentile
 * and ±1σ, ±2σ to draw the cone of uncertainty.
 */
function getTimelineSummary(timelineResults) {
  if (timelineResults.length === 0) return { years: [], median: [], minus2Sigma: [], minus1Sigma: [], plus1Sigma: [], plus2Sigma: [] };
  const numYears = timelineResults[0].length;
  const years = Array.from({ length: numYears }, (_, i) => i);
  const medians = [];
  const minus2Sigma = [];
  const minus1Sigma = [];
  const plus1Sigma = [];
  const plus2Sigma = [];

  for (let t = 0; t < numYears; t++) {
    const values = timelineResults.map((row) => row[t]);
    const m = mean(values);
    const sd = stdDev(values);
    medians.push(median(values));
    minus2Sigma.push(m - 2 * sd);
    minus1Sigma.push(m - sd);
    plus1Sigma.push(m + sd);
    plus2Sigma.push(m + 2 * sd);
  }

  return { years, median: medians, minus2Sigma, minus1Sigma, plus1Sigma, plus2Sigma };
}

export { mean, median, stdDev, getSummary, getTimelineSummary };
