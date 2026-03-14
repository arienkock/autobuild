import test from "node:test";
import assert from "node:assert";
import { Variable } from "../js/variable.js";
import { Model } from "../js/model.js";
import { npvEvaluator } from "../js/npv-model.js";

test("NPV evaluator returns timeline of length years+1", () => {
  const evaluator = npvEvaluator(100, 5);
  const model = new Model(evaluator).setVariables([
    Variable.constant(0.1),
    Variable.constant(20),
  ]);
  const timeline = model.evaluate();
  assert.strictEqual(timeline.length, 6);
  assert.strictEqual(timeline[0], -100);
});

test("NPV timeline year 0 is minus initial investment", () => {
  const evaluator = npvEvaluator(50, 3);
  const model = new Model(evaluator).setVariables([
    Variable.constant(0),
    Variable.constant(0),
  ]);
  const timeline = model.evaluate();
  assert.strictEqual(timeline[0], -50);
});

test("NPV with constant cashflow and zero rate increases linearly", () => {
  const evaluator = npvEvaluator(100, 2);
  const model = new Model(evaluator).setVariables([
    Variable.constant(0),
    Variable.constant(60),
  ]);
  const timeline = model.evaluate();
  // Year 0: -100; Year 1: -100 + 60 = -40; Year 2: -40 + 60 = 20
  assert.strictEqual(timeline[0], -100);
  assert.strictEqual(timeline[1], -40);
  assert.strictEqual(timeline[2], 20);
});
