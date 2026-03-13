import test from 'node:test';
import assert from 'node:assert';
import { runSimulation } from '../simulation.js';
import { createSumModel } from '../model.js';
import { createNPVModel } from '../npvModel.js';
import { constant } from '../variable.js';

test('runSimulation scalar returns summary', () => {
  const model = createSumModel([constant(5)]);
  const out = runSimulation(10, model);
  assert.strictEqual(out.resultShape, 'scalar');
  assert.strictEqual(out.summary.mean, 5);
  assert.strictEqual(out.summary.median, 5);
});

test('runSimulation timeline returns timeline summary', () => {
  const model = createNPVModel({
    initialInvestment: constant(100),
    cashflows: constant(50),
    discountRate: constant(0),
    years: 2,
  });
  const out = runSimulation(5, model);
  assert.strictEqual(out.resultShape, 'timeline');
  assert.strictEqual(out.summary.yearCount, 3);
  assert.strictEqual(out.summary.median.length, 3);
});
