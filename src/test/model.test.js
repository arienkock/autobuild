import test from "node:test";
import assert from "node:assert";
import { Variable } from "../js/variable.js";
import { Model } from "../js/model.js";

test("default model sums variable samples", () => {
  const model = new Model();
  model.addVariable(Variable.constant(1)).addVariable(Variable.constant(2));
  assert.strictEqual(model.evaluate(), 3);
  assert.strictEqual(model.evaluate(), 3);
});

test("model with setVariables", () => {
  const model = new Model();
  model.setVariables([Variable.constant(5), Variable.constant(3)]);
  assert.strictEqual(model.evaluate(), 8);
});

test("custom evaluator", () => {
  const model = new Model((vars) => vars.reduce((p, v) => p * v.sample(), 1));
  model.addVariable(Variable.constant(2)).addVariable(Variable.constant(3));
  assert.strictEqual(model.evaluate(), 6);
});
