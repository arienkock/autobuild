import { run } from './monteCarlo.js';
import { createSumModel } from './model.js';
import { summary } from './statistics.js';
import { constant, uniformVar, normalVar } from './variable.js';

const defaultModel = createSumModel([
  constant(100),
  uniformVar(0, 50),
  normalVar(10, 5),
]);

function renderStats(summaryObj) {
  const frag = document.createDocumentFragment();
  const entries = [
    ['Mean', summaryObj.mean],
    ['Median', summaryObj.median],
    ['Std Dev', summaryObj.stdDev],
    ['Mean − 2σ', summaryObj.minus2Sigma],
    ['Mean − 1σ', summaryObj.minus1Sigma],
    ['Mean + 1σ', summaryObj.plus1Sigma],
    ['Mean + 2σ', summaryObj.plus2Sigma],
  ];
  entries.forEach(([label, value]) => {
    const dt = document.createElement('dt');
    dt.textContent = label;
    const dd = document.createElement('dd');
    dd.textContent = typeof value === 'number' ? value.toFixed(4) : value;
    frag.appendChild(dt);
    frag.appendChild(dd);
  });
  return frag;
}

function runSimulation(iterations, model) {
  const results = run(iterations, model);
  return summary(results);
}

document.getElementById('sim-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const iterations = Number(document.getElementById('iterations').value) || 10000;
  const resultsSection = document.getElementById('results');
  const statsEl = document.getElementById('stats');
  const s = runSimulation(iterations, defaultModel);
  statsEl.replaceChildren(renderStats(s));
  resultsSection.classList.remove('hidden');
});
