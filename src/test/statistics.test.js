import test from "node:test";
import assert from "node:assert";
import { mean, median, stdDev, getSummary, getTimelineSummary } from "../js/statistics.js";

test("mean of single value", () => {
  assert.strictEqual(mean([10]), 10);
});

test("mean of array", () => {
  assert.strictEqual(mean([1, 2, 3, 4, 5]), 3);
});

test("median odd length", () => {
  assert.strictEqual(median([1, 3, 2]), 2);
});

test("median even length", () => {
  assert.strictEqual(median([1, 2, 3, 4]), 2.5);
});

test("stdDev", () => {
  const arr = [2, 4, 4, 4, 5, 5, 7, 9];
  assert.ok(Math.abs(stdDev(arr) - 2) < 0.001);
});

test("getSummary has mean median stdDev and bands", () => {
  const results = [1, 2, 3, 4, 5];
  const s = getSummary(results);
  assert.strictEqual(s.mean, 3);
  assert.strictEqual(s.median, 3);
  assert.ok(s.stdDev > 0);
  assert.strictEqual(s.minus1StdDev, s.mean - s.stdDev);
  assert.strictEqual(s.plus1StdDev, s.mean + s.stdDev);
  assert.strictEqual(s.minus2StdDev, s.mean - 2 * s.stdDev);
  assert.strictEqual(s.plus2StdDev, s.mean + 2 * s.stdDev);
});

test("getTimelineSummary returns bands per year", () => {
  const timelineResults = [
    [0, 10, 20],
    [0, 12, 22],
    [0, 8, 18],
  ];
  const s = getTimelineSummary(timelineResults);
  assert.deepStrictEqual(s.years, [0, 1, 2]);
  assert.strictEqual(s.median.length, 3);
  assert.strictEqual(s.minus1Sigma.length, 3);
  assert.strictEqual(s.plus1Sigma.length, 3);
  assert.strictEqual(s.minus2Sigma.length, 3);
  assert.strictEqual(s.plus2Sigma.length, 3);
});

test("getTimelineSummary empty returns empty arrays", () => {
  const s = getTimelineSummary([]);
  assert.deepStrictEqual(s.years, []);
  assert.deepStrictEqual(s.median, []);
});
