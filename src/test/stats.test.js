import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mean, median, stddev, summary } from '../montecarlo/stats.js'

test('mean of [1, 2, 3, 4, 5]', () => {
  assert.equal(mean([1, 2, 3, 4, 5]), 3)
})

test('mean of single value', () => {
  assert.equal(mean([7]), 7)
})

test('median of odd-length array', () => {
  assert.equal(median([3, 1, 2]), 2)
})

test('median of even-length array', () => {
  assert.equal(median([1, 2, 3, 4]), 2.5)
})

test('stddev of uniform values is 0', () => {
  assert.equal(stddev([5, 5, 5, 5]), 0)
})

test('stddev of [2, 4, 4, 4, 5, 5, 7, 9] is 2', () => {
  assert.equal(stddev([2, 4, 4, 4, 5, 5, 7, 9]), 2)
})

test('summary contains all keys', () => {
  const s = summary([1, 2, 3, 4, 5])
  assert.ok('mean' in s)
  assert.ok('median' in s)
  assert.ok('stddev' in s)
  assert.ok('range1' in s)
  assert.ok('range2' in s)
})

test('summary range1 is mean +/- 1 stddev', () => {
  const values = [1, 2, 3, 4, 5]
  const s = summary(values)
  assert.equal(s.range1[0], s.mean - s.stddev)
  assert.equal(s.range1[1], s.mean + s.stddev)
})

test('summary range2 is mean +/- 2 stddev', () => {
  const values = [1, 2, 3, 4, 5]
  const s = summary(values)
  assert.equal(s.range2[0], s.mean - 2 * s.stddev)
  assert.equal(s.range2[1], s.mean + 2 * s.stddev)
})
