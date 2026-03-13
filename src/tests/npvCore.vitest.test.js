import { describe, it, expect } from "vitest";
import { createTriangularSampler, runNpvSimulation } from "../js/npvCore.js";

function withDeterministicRandom(sequence, fn) {
  const original = Math.random;
  let index = 0;
  Math.random = () => {
    const value = sequence[index % sequence.length];
    index += 1;
    return value;
  };
  try {
    fn();
  } finally {
    Math.random = original;
  }
}

describe("createTriangularSampler", () => {
  it("returns constant when min=mode=max", () => {
    const sampler = createTriangularSampler(10, 10, 10);
    withDeterministicRandom([0, 0.5, 1], () => {
      expect(sampler()).toBe(10);
      expect(sampler()).toBe(10);
      expect(sampler()).toBe(10);
    });
  });
});

describe("runNpvSimulation", () => {
  it("computes deterministic NPV with degenerate distributions", () => {
    const sampler0 = () => -100;
    const sampler1 = () => 60;
    const sampler2 = () => 60;
    const discountRate = 0.1;
    const iterations = 1;

    const result = runNpvSimulation({
      periods: [sampler0, sampler1, sampler2],
      discountRate,
      iterations,
    });

    const expected =
      -100 + 60 / (1 + discountRate) + 60 / Math.pow(1 + discountRate, 2);

    expect(result.mean).toBeCloseTo(expected, 12);
    expect(result.samples[0]).toBeCloseTo(expected, 12);
  });

  it("exposes percentile and probability helpers", () => {
    const sampler = () => 50;
    const discountRate = 0;
    const iterations = 5;

    const result = runNpvSimulation({
      periods: [sampler],
      discountRate,
      iterations,
    });

    expect(result.percentile(0.05)).toBeCloseTo(50, 12);
    expect(result.percentile(0.5)).toBeCloseTo(50, 12);
    expect(result.percentile(0.95)).toBeCloseTo(50, 12);
    expect(result.probability((x) => x >= 50)).toBeCloseTo(1, 12);
    expect(result.probability((x) => x > 50)).toBeCloseTo(0, 12);
  });
});

