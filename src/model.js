import { sample } from './variable.js';

export const RESULT_SHAPE = Object.freeze({ SCALAR: 'scalar', TIMELINE: 'timeline' });

export function createSumModel(variables) {
  return {
    resultShape: RESULT_SHAPE.SCALAR,
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
