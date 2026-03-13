let cached = null;

export function randomNormal() {
  if (cached !== null) {
    const value = cached;
    cached = null;
    return value;
  }
  let u = 0;
  let v = 0;
  while (u === 0) {
    u = Math.random();
  }
  while (v === 0) {
    v = Math.random();
  }
  const mag = Math.sqrt(-2 * Math.log(u));
  const z0 = mag * Math.cos(2 * Math.PI * v);
  const z1 = mag * Math.sin(2 * Math.PI * v);
  cached = z1;
  return z0;
}

export function randomNormalWith(mean, stdDev) {
  if (!Number.isFinite(mean)) {
    throw new TypeError("mean must be finite");
  }
  if (!Number.isFinite(stdDev) || stdDev < 0) {
    throw new TypeError("stdDev must be a non-negative finite number");
  }
  if (stdDev === 0) {
    return mean;
  }
  return mean + stdDev * randomNormal();
}
