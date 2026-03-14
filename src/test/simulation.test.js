import test from "node:test";
import assert from "node:assert";
import { Variable } from "../js/variable.js";
import { Model } from "../js/model.js";
import { runSimulation } from "../js/simulation.js";

test("runSimulation returns array of length iterations", () => {
  const model = new Model().addVariable(Variable.constant(1));
  const results = runSimulation(100, model);
  assert.strictEqual(results.length, 100);
  assert.strictEqual(results.every((r) => r === 1), true);
});

test("runSimulation returns all results for analysis", () => {
  const model = new Model()
    .addVariable(Variable.constant(1))
    .addVariable(Variable.constant(2));
  const results = runSimulation(50, model);
  assert.strictEqual(results.length, 50);
  assert.strictEqual(results.every((r) => r === 3), true);
});
