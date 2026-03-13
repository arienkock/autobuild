import test from 'node:test';
import assert from 'node:assert';
import {
  sample,
  constant,
  normalVar,
  uniformVar,
  triangularVar,
  paretoVar,
} from '../variable.js';

test('constant variable returns same value', () => {
  assert.strictEqual(sample(constant(42)), 42);
  assert.strictEqual(sample(constant(-1), Math.random), -1);
});

test('normal variable uses distribution', () => {
  const r = () => 0.5;
  const v = sample(normalVar(10, 1), r);
  assert.ok(typeof v === 'number');
});

test('uniform variable uses distribution', () => {
  const r = () => 0;
  assert.strictEqual(sample(uniformVar(5, 15), r), 5);
});

test('arbitrary with value', () => {
  assert.strictEqual(
    sample({ type: 'arbitrary', value: 7 }),
    7
  );
});

test('arbitrary with sample function', () => {
  const v = sample({
    type: 'arbitrary',
    sample: (r) => (r() < 0.5 ? 1 : 2),
  }, () => 0.1);
  assert.strictEqual(v, 1);
});
