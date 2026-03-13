import * as dist from './distributions.js';

export function sample(variable, random = Math.random) {
  if (variable.type === 'constant') {
    return variable.value;
  }
  if (variable.type === 'normal') {
    return dist.normal(variable.mean, variable.stdDev, random);
  }
  if (variable.type === 'uniform') {
    return dist.uniform(variable.min, variable.max, random);
  }
  if (variable.type === 'triangular') {
    return dist.triangular(variable.a, variable.b, variable.c, random);
  }
  if (variable.type === 'pareto') {
    return dist.pareto(variable.alpha, variable.xm, random);
  }
  if (variable.type === 'arbitrary' && typeof variable.sample === 'function') {
    return variable.sample(random);
  }
  if (variable.type === 'arbitrary' && 'value' in variable) {
    return variable.value;
  }
  throw new Error(`Unknown variable type: ${variable.type}`);
}

export function constant(value) {
  return { type: 'constant', value };
}

export function normalVar(mean, stdDev) {
  return { type: 'normal', mean, stdDev };
}

export function uniformVar(min, max) {
  return { type: 'uniform', min, max };
}

export function triangularVar(a, b, c) {
  return { type: 'triangular', a, b, c };
}

export function paretoVar(alpha, xm) {
  return { type: 'pareto', alpha, xm };
}
