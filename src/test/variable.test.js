import test from "node:test";
import assert from "node:assert";
import { Variable } from "../js/variable.js";

test("constant always returns same value", () => {
  const v = Variable.constant(42);
  assert.strictEqual(v.sample(), 42);
  assert.strictEqual(v.sample(), 42);
});

test("distribution returns number from sampler", () => {
  const v = Variable.distribution(() => 7);
  assert.strictEqual(v.sample(), 7);
});

test("arbitrary with function uses function", () => {
  let n = 0;
  const v = Variable.arbitrary(() => ++n);
  assert.strictEqual(v.sample(), 1);
  assert.strictEqual(v.sample(), 2);
});

test("arbitrary with array samples from array", () => {
  const v = Variable.arbitrary([10, 20, 30]);
  for (let i = 0; i < 50; i++) {
    const s = v.sample();
    assert.ok([10, 20, 30].includes(s));
  }
});
