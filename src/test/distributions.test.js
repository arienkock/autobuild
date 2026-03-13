import test from 'node:test';
import assert from 'node:assert';
import {
  uniform,
  normal,
  triangular,
  pareto,
} from '../distributions.js';

test('uniform returns value in [min, max) with mock random', () => {
  let i = 0;
  const r = () => [0, 0.5, 1][i++];
  assert.strictEqual(uniform(10, 20, r), 10);
  assert.strictEqual(uniform(10, 20, r), 15);
  assert.strictEqual(uniform(10, 20, r), 20);
});

test('normal returns value with correct mean for deterministic random', () => {
  const r = () => 0.5;
  const z = Math.sqrt(-2 * Math.log(0.5)) * Math.cos(2 * Math.PI * 0.5);
  assert.strictEqual(normal(100, 5, r), 100 + 5 * z);
});

test('triangular with a<=c<=b', () => {
  const r = () => 0.25;
  const v = triangular(0, 10, 5, r);
  assert.ok(v >= 0 && v <= 10);
});

test('pareto returns value >= xm', () => {
  const r = () => 0.5;
  const v = pareto(2, 1, r);
  assert.ok(v >= 1);
});
