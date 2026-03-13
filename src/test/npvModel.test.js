import test from 'node:test';
import assert from 'node:assert';
import { createNPVModel, computeNPVTimeline } from '../npvModel.js';
import { constant } from '../variable.js';

test('computeNPVTimeline: initial only', () => {
  const timeline = computeNPVTimeline(100, 0.1, []);
  assert.deepStrictEqual(timeline, [-100]);
});

test('computeNPVTimeline: one year cashflow', () => {
  const timeline = computeNPVTimeline(100, 0, [110]);
  assert.strictEqual(timeline.length, 2);
  assert.strictEqual(timeline[0], -100);
  assert.strictEqual(timeline[1], -100 + 110);
});

test('computeNPVTimeline: discounting', () => {
  const timeline = computeNPVTimeline(100, 0.1, [0, 121]);
  assert.strictEqual(timeline.length, 3);
  assert.strictEqual(timeline[0], -100);
  const pv1 = 121 / (1.1 * 1.1);
  assert.ok(Math.abs(timeline[2] - (-100 + pv1)) < 1e-10);
});

test('createNPVModel returns timeline shape', () => {
  const model = createNPVModel({
    initialInvestment: constant(100),
    cashflows: constant(10),
    discountRate: constant(0.1),
    years: 2,
  });
  assert.strictEqual(model.resultShape, 'timeline');
  const timeline = model.run(() => 0.5);
  assert.ok(Array.isArray(timeline));
  assert.strictEqual(timeline.length, 3);
  assert.strictEqual(timeline[0], -100);
});

test('createNPVModel with constant inputs is deterministic', () => {
  const model = createNPVModel({
    initialInvestment: constant(1000),
    cashflows: constant(200),
    discountRate: constant(0.1),
    years: 3,
  });
  const t1 = model.run(() => 0.1);
  const t2 = model.run(() => 0.9);
  assert.deepStrictEqual(t1, t2);
});
