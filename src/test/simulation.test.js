import { describe, it } from "node:test";
import assert from "node:assert";
import { runSimulation } from "../js/simulation.js";
import { sumModel } from "../js/model.js";
import { constant } from "../js/variable.js";
import { uniform } from "../js/distributions.js";
import { sampled } from "../js/variable.js";

describe("runSimulation", () => {
  it("returns array of length iterations", () => {
    const model = sumModel([constant(1)]);
    const results = runSimulation(model, 100);
    assert.strictEqual(results.length, 100);
  });

  it("with constant model all results are equal", () => {
    const model = sumModel([constant(3), constant(5)]);
    const results = runSimulation(model, 50);
    assert.ok(results.every((r) => r === 8));
  });

  it("with sampled variable results vary", () => {
    const model = sumModel([constant(0), sampled(uniform(0, 10))]);
    const results = runSimulation(model, 200);
    const unique = new Set(results);
    assert.ok(unique.size > 1);
    assert.ok(results.every((r) => r >= 0 && r <= 10));
  });

  it("returns all results for analysis", () => {
    const model = sumModel([constant(1)]);
    const results = runSimulation(model, 5);
    assert.deepStrictEqual(results, [1, 1, 1, 1, 1]);
  });
});
