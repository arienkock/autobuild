import { describe, it } from "node:test";
import assert from "node:assert";
import { sumModel } from "../js/model.js";
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
