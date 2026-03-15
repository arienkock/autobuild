import { describe, it } from "node:test";
import assert from "node:assert";
import { sumModel, npvModel } from "../js/model.js";
import { constant } from "../js/variable.js";

describe("sumModel", () => {
  it("evaluate returns sum of variable samples", () => {
    const model = sumModel([constant(3), constant(5)]);
    assert.strictEqual(model.evaluate(), 8);
    assert.strictEqual(model.evaluate(), 8);
  });

  it("evaluate with single variable returns that value", () => {
    const model = sumModel([constant(100)]);
    assert.strictEqual(model.evaluate(), 100);
  });

  it("evaluate with empty variables returns 0", () => {
    const model = sumModel([]);
    assert.strictEqual(model.evaluate(), 0);
  });
});

describe("npvModel", () => {
  it("returns timeline with year 0 = -initialInvestment", () => {
    const model = npvModel({
      initialInvestment: constant(1000),
      discountRate: constant(0.1),
      cashflows: [constant(100)],
    });
    const timeline = model.evaluate();
    assert.strictEqual(timeline.length, 2);
    assert.strictEqual(timeline[0], -1000);
  });

  it("computes NPV at year 1 as -I + CF1/(1+r)", () => {
    const model = npvModel({
      initialInvestment: constant(1000),
      discountRate: constant(0.1),
      cashflows: [constant(200)],
    });
    const timeline = model.evaluate();
    const expectedYear1 = -1000 + 200 / 1.1;
    assert.ok(Math.abs(timeline[1] - expectedYear1) < 1e-6);
  });

  it("timeline length is cashflows.length + 1", () => {
    const model = npvModel({
      initialInvestment: constant(500),
      discountRate: constant(0.05),
      cashflows: [constant(100), constant(100), constant(100)],
    });
    const timeline = model.evaluate();
    assert.strictEqual(timeline.length, 4);
    assert.strictEqual(timeline[0], -500);
  });
});
