function uniform(a, b) {
  return function () {
    return a + (b - a) * Math.random();
  };
}

function normal(mean, stdDev) {
  return function () {
    const u1 = Math.random();
    const u2 = Math.random();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    return mean + stdDev * z;
  };
}

function triangular(a, b, c) {
  return function () {
    const u = Math.random();
    const F = (c - a) / (b - a);
    if (u < F) {
      return a + Math.sqrt(u * (b - a) * (c - a));
    }
    return b - Math.sqrt((1 - u) * (b - a) * (b - c));
  };
}

function pareto(alpha, xm) {
  return function () {
    return xm / Math.pow(Math.random(), 1 / alpha);
  };
}

export { uniform, normal, triangular, pareto };
