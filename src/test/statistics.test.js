import test from 'node:test';
import assert from 'node:assert';
import { mean, median, stdDev, summary, timelineSummary } from '../statistics.js';

test('mean of single value', () => {
  assert.strictEqual(mean([5]), 5);
});

test('mean of multiple values', () => {
  assert.strictEqual(mean([1, 2, 3, 4, 5]), 3);
});

test('median odd length', () => {
  assert.strictEqual(median([1, 3, 5]), 3);
});

test('median even length', () => {
  assert.strictEqual(median([1, 2, 3, 4]), 2.5);
});

test('stdDev of constant array', () => {
  assert.strictEqual(stdDev([7, 7, 7]), 0);
});

test('stdDev of spread', () => {
  const values = [2, 4, 4, 4, 5, 5, 7, 9];
  const m = mean(values);
  assert.ok(stdDev(values) > 0);
});

test('summary contains mean median stdDev and sigma bounds', () => {
  const values = [1, 2, 3, 4, 5];
  const s = summary(values);
  assert.strictEqual(s.mean, 3);
  assert.strictEqual(s.median, 3);
  assert.ok(s.stdDev >= 0);
  assert.strictEqual(s.minus1Sigma, 3 - s.stdDev);
  assert.strictEqual(s.plus1Sigma, 3 + s.stdDev);
  assert.strictEqual(s.minus2Sigma, 3 - 2 * s.stdDev);
  assert.strictEqual(s.plus2Sigma, 3 + 2 * s.stdDev);
});

test('timelineSummary returns per-year stats', () => {
  const timelines = [
    [0, 10, 20],
    [2, 12, 22],
    [4, 14, 24],
  ];
  const s = timelineSummary(timelines);
  assert.strictEqual(s.yearCount, 3);
  assert.strictEqual(s.median[0], 2);
  assert.strictEqual(s.median[1], 12);
  assert.strictEqual(s.median[2], 22);
  assert.strictEqual(s.minus1Sigma.length, 3);
  assert.strictEqual(s.plus2Sigma.length, 3);
});

test('timelineSummary empty returns zeros', () => {
  const s = timelineSummary([]);
  assert.strictEqual(s.yearCount, 0);
  assert.deepStrictEqual(s.median, []);
});
