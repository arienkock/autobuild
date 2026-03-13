import test from 'node:test';
import assert from 'node:assert';
import { run } from '../monteCarlo.js';
import { createSumModel } from '../model.js';
import { constant } from '../variable.js';

test('run returns array of length iterations', () => {
  const model = createSumModel([constant(1)]);
  const results = run(100, model);
  assert.strictEqual(results.length, 100);
});

test('run with constant model returns same value every time', () => {
  const model = createSumModel([constant(7)]);
  const results = run(10, model);
  assert.deepStrictEqual(results, [7, 7, 7, 7, 7, 7, 7, 7, 7, 7]);
});

test('run uses provided random when deterministic', () => {
  const model = createSumModel([constant(1), constant(2)]);
  let callCount = 0;
  const r = () => (callCount++ % 2 === 0 ? 0 : 1);
  const results = run(3, model, r);
  assert.strictEqual(results.length, 3);
  assert.strictEqual(results[0], 3);
  assert.strictEqual(results[1], 3);
  assert.strictEqual(results[2], 3);
});
