export function analyze(data) {
  const n = data.length;
  if (n === 0) return null;

  const sorted = [...data].sort((a, b) => a - b);
  
  const sum = data.reduce((acc, val) => acc + val, 0);
  const mean = sum / n;

  const median = n % 2 === 0
    ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
    : sorted[Math.floor(n / 2)];

  const variance = data.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / (n - 1);
  const stdDev = Math.sqrt(variance);

  return {
    mean,
    median,
    stdDev,
    intervals: {
      oneStdDev: [mean - stdDev, mean + stdDev],
      twoStdDev: [mean - 2 * stdDev, mean + 2 * stdDev]
    }
  };
}
