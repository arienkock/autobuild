import { Simulation } from './src/simulation.js';
import { SumModel } from './src/model.js';
import { Normal, Uniform, Constant } from './src/distributions.js';
import { analyze } from './src/statistics.js';

document.getElementById('runBtn').addEventListener('click', () => {
  const iterations = parseInt(document.getElementById('iterations').value, 10);
  
  const model = new SumModel([
    new Normal(100, 15),
    new Uniform(10, 20),
    new Constant(5)
  ]);

  const sim = new Simulation();
  const results = sim.run(iterations, model);
  const stats = analyze(results);

  const resultsDiv = document.getElementById('results');
  
  if (stats) {
    resultsDiv.innerHTML = `
      <p><strong>Mean:</strong> ${stats.mean.toFixed(4)}</p>
      <p><strong>Median:</strong> ${stats.median.toFixed(4)}</p>
      <p><strong>Standard Deviation:</strong> ${stats.stdDev.toFixed(4)}</p>
      <p><strong>68% Interval (1 SD):</strong> [${stats.intervals.oneStdDev[0].toFixed(4)}, ${stats.intervals.oneStdDev[1].toFixed(4)}]</p>
      <p><strong>95% Interval (2 SD):</strong> [${stats.intervals.twoStdDev[0].toFixed(4)}, ${stats.intervals.twoStdDev[1].toFixed(4)}]</p>
    `;
  } else {
    resultsDiv.innerHTML = '<p>No results to display.</p>';
  }
});
