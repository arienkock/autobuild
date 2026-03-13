import test from 'node:test';
import assert from 'node:assert';
import { createSumModel } from '../model.js';
import { constant } from '../variable.js';

test('sum model adds constant variables', () => {
  const model = createSumModel([constant(1), constant(2), constant(3)]);
  assert.strictEqual(model.run(() => 0), 6);
});

test('compute takes pre-sampled values', () => {
  const model = createSumModel([constant(0), constant(0)]);
  assert.strictEqual(model.compute([10, 20]), 30);
});

test('run samples then computes', () => {
  const model = createSumModel([constant(5), constant(5)]);
  assert.strictEqual(model.run(() => 0.5), 10);
});
