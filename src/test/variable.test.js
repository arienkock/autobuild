import { describe, it } from "node:test";
import assert from "node:assert";
import { constant, sampled, arbitrary } from "../js/variable.js";

describe("constant", () => {
  it("sample always returns same value", () => {
    const v = constant(7);
    assert.strictEqual(v.sample(), 7);
    assert.strictEqual(v.sample(), 7);
  });
});

describe("sampled", () => {
  it("sample returns value from sampler", () => {
    let n = 0;
    const v = sampled(() => ++n);
    assert.strictEqual(v.sample(), 1);
    assert.strictEqual(v.sample(), 2);
  });
});

describe("arbitrary", () => {
  it("sample returns given value", () => {
    const v = arbitrary(42);
    assert.strictEqual(v.sample(), 42);
  });
});
