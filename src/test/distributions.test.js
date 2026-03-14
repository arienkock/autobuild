import test from "node:test";
import assert from "node:assert";
import { uniform, normal, triangular, pareto } from "../js/distributions.js";

test("uniform returns values in [a, b]", () => {
  const sample = uniform(10, 20);
  for (let i = 0; i < 100; i++) {
    const v = sample();
    assert.ok(v >= 10 && v <= 20);
  }
});

test("normal returns numbers", () => {
  const sample = normal(5, 2);
  for (let i = 0; i < 100; i++) {
    assert.strictEqual(typeof sample(), "number");
  }
});

test("triangular returns values in [a, b]", () => {
  const sample = triangular(0, 10, 5);
  for (let i = 0; i < 100; i++) {
    const v = sample();
    assert.ok(v >= 0 && v <= 10);
  }
});

test("pareto returns values >= xm", () => {
  const sample = pareto(2, 1);
  for (let i = 0; i < 100; i++) {
    assert.ok(sample() >= 1);
  }
});
