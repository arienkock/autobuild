import { test } from 'node:test'
import assert from 'node:assert/strict'
import { simulate } from '../montecarlo/simulate.js'
import { Model } from '../montecarlo/model.js'
import { Constant } from '../montecarlo/variables.js'

test('simulate returns array of correct length', () => {
  const model = new Model([new Constant(1)])
  assert.equal(simulate(model, 100).length, 100)
})

test('simulate returns all evaluations', () => {
  const model = new Model([new Constant(5)])
  const results = simulate(model, 50)
  assert.ok(results.every(v => v === 5))
})

test('simulate calls model.evaluate for each iteration', () => {
  let count = 0
  const model = { evaluate: () => ++count }
  simulate(model, 10)
  assert.equal(count, 10)
})

test('simulate with 0 iterations returns empty array', () => {
  const model = new Model([new Constant(1)])
  assert.deepEqual(simulate(model, 0), [])
})
