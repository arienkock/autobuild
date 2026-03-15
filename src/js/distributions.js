export function uniform(min, max) {
  return () => min + Math.random() * (max - min);
}

export function normal(mean, stdDev) {
  return () => {
    const u1 = Math.random();
    const u2 = Math.random();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mean + stdDev * z;
  };
}

export function triangular(min, mode, max) {
  return () => {
    const u = Math.random();
    const c = (mode - min) / (max - min);
    if (u <= c) return min + Math.sqrt(u * (max - min) * (mode - min));
    return max - Math.sqrt((1 - u) * (max - min) * (max - mode));
  };
}

export function pareto(xm, alpha) {
  return () => xm / Math.pow(Math.random(), 1 / alpha);
}
