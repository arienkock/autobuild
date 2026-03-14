import test from 'node:test';
import assert from 'node:assert';
import { Simulation } from '../src/simulation.js';
import { SumModel } from '../src/model.js';
import { Constant, Normal, Uniform } from '../src/distributions.js';
import { analyze } from '../src/statistics.js';

test('Constant distribution returns fixed value', () => {
  const constant = new Constant(10);
  assert.strictEqual(constant.sample(), 10);
});

test('Normal distribution returns numbers', () => {
  const normal = new Normal(0, 1);
  const value = normal.sample();
  assert.strictEqual(typeof value, 'number');
});

test('Uniform distribution returns numbers within range', () => {
  const uniform = new Uniform(5, 10);
  for (let i = 0; i < 100; i++) {
    const value = uniform.sample();
    assert.ok(value >= 5 && value <= 10);
  }
});

test('SumModel sums variable samples', () => {
  const model = new SumModel([new Constant(2), new Constant(3)]);
  assert.strictEqual(model.run(), 5);
});

test('Simulation runs for specified iterations', () => {
  const sim = new Simulation();
  const model = new SumModel([new Constant(1)]);
  const results = sim.run(100, model);
  assert.strictEqual(results.length, 100);
  results.forEach(r => assert.strictEqual(r, 1));
});

test('analyze calculates correct statistics', () => {
  const results = [10, 20, 30];
  const stats = analyze(results);
  
  assert.strictEqual(stats.mean, 20);
  assert.strictEqual(stats.median, 20);
  
  const expectedViance = ((10-20)**2 + (20-20)**2 + (30-20)**2) / 2; 
  const expectedStdDev = Math.sqrt(expectedViance);
  
  assert.ok(Math.abs(stats.stdDev - expectedStdDev) < 0.0001);
  assert.deepStrictEqual(stats.intervals, {
    oneStdDev: [20 - expectedStdDev, 20 + expectedStdDev],
    twoStdDev: [20 - 2 * expectedStdDev, 20 + 2 * expectedStdDev]
  });
});
