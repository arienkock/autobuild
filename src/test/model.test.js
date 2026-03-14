import { test } from 'node:test'
import assert from 'node:assert/strict'
import { Model } from '../montecarlo/model.js'
import { Constant, Arbitrary } from '../montecarlo/variables.js'

test('Model with no variables evaluates to 0', () => {
  assert.equal(new Model([]).evaluate(), 0)
})

test('Model sums constant variables', () => {
  const model = new Model([new Constant(3), new Constant(7)])
  assert.equal(model.evaluate(), 10)
})

test('Model evaluate calls each variable once per call', () => {
  let count = 0
  const model = new Model([new Arbitrary(() => { count++; return 1 }), new Arbitrary(() => { count++; return 1 })])
  model.evaluate()
  assert.equal(count, 2)
  model.evaluate()
  assert.equal(count, 4)
})
