import { test } from 'node:test'
import assert from 'node:assert/strict'
import { Constant, Arbitrary, Uniform, Normal, Triangular, Pareto, Variable } from '../montecarlo/variables.js'

test('Variable base class throws on sample()', () => {
  assert.throws(() => new Variable().sample(), /not implemented/)
})

test('Constant always returns the same value', () => {
  const c = new Constant(42)
  for (let i = 0; i < 10; i++) assert.equal(c.sample(), 42)
})

test('Arbitrary delegates to provided function', () => {
  let n = 0
  const a = new Arbitrary(() => ++n)
  assert.equal(a.sample(), 1)
  assert.equal(a.sample(), 2)
})

test('Uniform samples within [min, max]', () => {
  const u = new Uniform(10, 20)
  for (let i = 0; i < 100; i++) {
    const v = u.sample()
    assert.ok(v >= 10 && v <= 20, `${v} out of [10, 20]`)
  }
})

test('Normal mean converges', () => {
  const n = new Normal(100, 10)
  const samples = Array.from({ length: 10000 }, () => n.sample())
  const m = samples.reduce((s, v) => s + v, 0) / samples.length
  assert.ok(Math.abs(m - 100) < 1, `mean ${m} too far from 100`)
})

test('Triangular samples within [min, max]', () => {
  const t = new Triangular(0, 5, 10)
  for (let i = 0; i < 100; i++) {
    const v = t.sample()
    assert.ok(v >= 0 && v <= 10, `${v} out of [0, 10]`)
  }
})

test('Triangular mode is most likely region', () => {
  const t = new Triangular(0, 9, 10)
  const samples = Array.from({ length: 10000 }, () => t.sample())
  const m = samples.reduce((s, v) => s + v, 0) / samples.length
  assert.ok(m > 5, `mean ${m} should be above midpoint for mode=9`)
})

test('Pareto samples are >= scale', () => {
  const p = new Pareto(1, 2)
  for (let i = 0; i < 100; i++) {
    const v = p.sample()
    assert.ok(v >= 1, `${v} below scale 1`)
  }
})
