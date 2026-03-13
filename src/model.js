import { sample } from './variable.js';

export function createSumModel(variables) {
  return {
    variables,
    compute(sampledValues) {
      return sampledValues.reduce((a, b) => a + b, 0);
    },
    run(random = Math.random) {
      const values = this.variables.map((v) => sample(v, random));
      return this.compute(values);
    },
  };
}
