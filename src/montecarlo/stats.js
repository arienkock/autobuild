export function mean(values) {
  return values.reduce((s, v) => s + v, 0) / values.length
}

export function median(values) {
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid]
}

export function stddev(values) {
  const m = mean(values)
  return Math.sqrt(values.reduce((s, v) => s + (v - m) ** 2, 0) / values.length)
}

export function summary(values) {
  const m = mean(values)
  const s = stddev(values)
  return {
    mean: m,
    median: median(values),
    stddev: s,
    range1: [m - s, m + s],
    range2: [m - 2 * s, m + 2 * s],
  }
}
