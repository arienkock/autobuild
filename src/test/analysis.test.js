import { describe, it } from "node:test";
import assert from "node:assert";
import { computeStats } from "../js/analysis.js";

describe("computeStats", () => {
  it("returns mean, median, stdDev and bands for single value", () => {
    const results = [10];
    const stats = computeStats(results);
    assert.strictEqual(stats.mean, 10);
    assert.strictEqual(stats.median, 10);
    assert.strictEqual(stats.stdDev, 0);
    assert.strictEqual(stats.band1Lower, 10);
    assert.strictEqual(stats.band1Upper, 10);
    assert.strictEqual(stats.band2Lower, 10);
    assert.strictEqual(stats.band2Upper, 10);
  });

  it("returns correct mean and median for even count", () => {
    const results = [2, 4, 6, 8];
    const stats = computeStats(results);
    assert.strictEqual(stats.mean, 5);
    assert.strictEqual(stats.median, 5);
  });

  it("returns correct mean and median for odd count", () => {
    const results = [1, 3, 5];
    const stats = computeStats(results);
    assert.strictEqual(stats.mean, 3);
    assert.strictEqual(stats.median, 3);
  });

  it("returns correct stdDev and bands", () => {
    const results = [2, 4, 4, 4, 4, 6];
    const stats = computeStats(results);
    assert.ok(Math.abs(stats.mean - 4) < 0.001);
    assert.ok(stats.stdDev > 0);
    assert.strictEqual(stats.band1Lower, stats.mean - stats.stdDev);
    assert.strictEqual(stats.band1Upper, stats.mean + stats.stdDev);
    assert.strictEqual(stats.band2Lower, stats.mean - 2 * stats.stdDev);
    assert.strictEqual(stats.band2Upper, stats.mean + 2 * stats.stdDev);
  });
});
