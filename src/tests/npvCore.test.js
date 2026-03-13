import { test, assertApproxEqual, assertEqual } from "./testRunner.js";
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

test("createTriangularSampler returns constant when min=mode=max", () => {
  const sampler = createTriangularSampler(10, 10, 10);
  withDeterministicRandom([0, 0.5, 1], () => {
    assertEqual(sampler(), 10);
    assertEqual(sampler(), 10);
    assertEqual(sampler(), 10);
  });
});

test("runNpvSimulation computes deterministic NPV with degenerate distributions", () => {
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
  assertApproxEqual(result.mean, expected, 1e-12);
  assertApproxEqual(result.samples[0], expected, 1e-12);
});

test("runNpvSimulation exposes percentile and probability helpers", () => {
  const sampler = () => 50;
  const discountRate = 0;
  const iterations = 5;
  const result = runNpvSimulation({
    periods: [sampler],
    discountRate,
    iterations,
  });
  assertApproxEqual(result.percentile(0.05), 50, 1e-12);
  assertApproxEqual(result.percentile(0.5), 50, 1e-12);
  assertApproxEqual(result.percentile(0.95), 50, 1e-12);
  assertApproxEqual(result.probability((x) => x >= 50), 1, 1e-12);
  assertApproxEqual(result.probability((x) => x > 50), 0, 1e-12);
});

