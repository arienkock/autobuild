export function uniform(min, max, random = Math.random) {
  return min + (max - min) * random();
}

export function normal(mean, stdDev, random = Math.random) {
  const u1 = random();
  const u2 = random();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return mean + stdDev * z;
}

export function triangular(a, b, c, random = Math.random) {
  const u = random();
  const F = (c - a) / (b - a);
  if (u < F) {
    return a + Math.sqrt(u * (b - a) * (c - a));
  }
  return b - Math.sqrt((1 - u) * (b - a) * (b - c));
}

export function pareto(alpha, xm, random = Math.random) {
  return xm / Math.pow(random(), 1 / alpha);
}
