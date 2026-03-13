export function createTriangularSampler(min, mode, max) {
  if (!Number.isFinite(min) || !Number.isFinite(mode) || !Number.isFinite(max)) {
    throw new Error("Non-finite triangular parameters");
  }
  if (!(min <= mode && mode <= max)) {
    throw new Error("Triangular parameters must satisfy min ≤ mode ≤ max");
  }
  if (min === max) {
    return () => min;
  }
  const range = max - min;
  const c = (mode - min) / range;
  return () => {
    const u = Math.random();
    if (u < c) {
      return min + Math.sqrt(u * range * (mode - min));
    }
    return max - Math.sqrt((1 - u) * range * (max - mode));
  };
}

export function runNpvSimulation(options) {
  const { periods, discountRate, iterations } = options;
  if (!Array.isArray(periods) || periods.length === 0) {
    throw new Error("At least one period is required");
  }
  if (!Number.isFinite(discountRate)) {
    throw new Error("Discount rate must be finite");
  }
  if (!Number.isInteger(iterations) || iterations <= 0) {
    throw new Error("Iterations must be a positive integer");
  }
  const samplers = periods.map((p, index) => {
    if (typeof p !== "function") {
      throw new Error(`Period at index ${index} is not a sampler`);
    }
    return p;
  });

  const n = iterations;
  const samples = new Float64Array(n);
  let sum = 0;
  let sumSq = 0;
  const discountFactor = 1 + discountRate;

  for (let i = 0; i < n; i++) {
    let t = 0;
    let npv = 0;
    for (const sampler of samplers) {
      const cf = sampler();
      const discounted = cf / Math.pow(discountFactor, t);
      npv += discounted;
      t += 1;
    }
    samples[i] = npv;
    sum += npv;
    sumSq += npv * npv;
  }

  const mean = sum / n;
  const variance = n > 1 ? (sumSq - n * mean * mean) / (n - 1) : 0;
  const stdDev = Math.sqrt(Math.max(variance, 0));

  const sorted = Array.from(samples).sort((a, b) => a - b);

  function percentile(p) {
    if (p <= 0) return sorted[0];
    if (p >= 1) return sorted[sorted.length - 1];
    const index = (sorted.length - 1) * p;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    if (lower === upper) {
      return sorted[lower];
    }
    const weight = index - lower;
    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
  }

  function probability(predicate) {
    let count = 0;
    for (let i = 0; i < samples.length; i++) {
      if (predicate(samples[i])) {
        count += 1;
      }
    }
    return count / samples.length;
  }

  return {
    samples,
    mean,
    stdDev,
    percentile,
    probability,
  };
}

