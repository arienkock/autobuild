import { describe, it } from "node:test";
import assert from "node:assert";
import { uniform, normal, triangular, pareto } from "../js/distributions.js";

describe("uniform", () => {
  it("returns value within [min, max]", () => {
    for (let i = 0; i < 100; i++) {
      const v = uniform(0, 10)();
      assert.ok(v >= 0 && v <= 10);
    }
  });
});

describe("normal", () => {
  it("returns values centered near mean", () => {
    const samples = Array.from({ length: 1000 }, () => normal(5, 1)());
    const mean = samples.reduce((a, b) => a + b, 0) / samples.length;
    assert.ok(mean > 4.5 && mean < 5.5);
  });
});

describe("triangular", () => {
  it("returns value within [min, max]", () => {
    for (let i = 0; i < 100; i++) {
      const v = triangular(0, 5, 10)();
      assert.ok(v >= 0 && v <= 10);
    }
  });
});

describe("pareto", () => {
  it("returns value >= xm", () => {
    for (let i = 0; i < 100; i++) {
      const v = pareto(1, 2)();
      assert.ok(v >= 1);
    }
  });
});
