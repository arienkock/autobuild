/**
 * Top-level simulation orchestration.
 * Models implement { resultShape: 'scalar'|'timeline', run(random): number|number[] }.
 * Raw results are aggregated into either a scalar summary or a timeline summary.
 */

import { run } from './monteCarlo.js';
import { summary, timelineSummary } from './statistics.js';

/**
 * @param {number} iterations
 * @param {{ resultShape: 'scalar'|'timeline', run: (random: () => number) => number|number[] }} model
 * @param {() => number} [random]
 * @returns {{ resultShape: 'scalar', summary: import('./statistics.js').Summary } | { resultShape: 'timeline', summary: import('./statistics.js').TimelineSummary }}
 */
export function runSimulation(iterations, model, random = Math.random) {
  const raw = run(iterations, model, random);
  if (model.resultShape === 'timeline') {
    return { resultShape: 'timeline', summary: timelineSummary(/** @type {number[][]} */ (raw)) };
  }
  return { resultShape: 'scalar', summary: summary(/** @type {number[]} */ (raw)) };
}
