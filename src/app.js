import { runSimulation } from './simulation.js';
import { createSumModel } from './model.js';
import { createNPVModel } from './npvModel.js';
import { renderConeChart } from './coneChart.js';
import { constant, uniformVar, normalVar } from './variable.js';

const defaultSumModel = createSumModel([
  constant(100),
  uniformVar(0, 50),
  normalVar(10, 5),
]);

function getSelectedModel() {
  const modelType = document.getElementById('model-type').value;
  if (modelType === 'npv') {
    const initial = Number(document.getElementById('npv-initial').value) || 1000;
    const years = Math.max(1, Math.min(50, Number(document.getElementById('npv-years').value) || 10));
    const cfMean = Number(document.getElementById('npv-cf-mean').value) || 200;
    const cfStd = Number(document.getElementById('npv-cf-std').value) || 0;
    const rate = Number(document.getElementById('npv-rate').value) ?? 0.1;
    const cashflow = cfStd > 0 ? normalVar(cfMean, cfStd) : constant(cfMean);
    return createNPVModel({
      initialInvestment: constant(initial),
      cashflows: cashflow,
      discountRate: constant(rate),
      years,
    });
  }
  return defaultSumModel;
}

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

function showScalarResults(summary) {
  document.getElementById('results-scalar').classList.remove('hidden');
  document.getElementById('results-timeline').classList.add('hidden');
  const statsEl = document.getElementById('stats');
  statsEl.replaceChildren(renderStats(summary));
}

function showTimelineResults(summary) {
  document.getElementById('results-scalar').classList.add('hidden');
  document.getElementById('results-timeline').classList.remove('hidden');
  const container = document.getElementById('chart-container');
  container.replaceChildren(renderConeChart(summary));
}

function getIterations() {
  const modelType = document.getElementById('model-type').value;
  const id = modelType === 'npv' ? 'iterations-npv' : 'iterations';
  return Number(document.getElementById(id).value) || (modelType === 'npv' ? 5000 : 10000);
}

document.getElementById('model-type').addEventListener('change', () => {
  const isNpv = document.getElementById('model-type').value === 'npv';
  document.getElementById('form-sum').classList.toggle('hidden', isNpv);
  document.getElementById('form-npv').classList.toggle('hidden', !isNpv);
});

document.getElementById('sim-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const model = getSelectedModel();
  const iterations = getIterations();
  const result = runSimulation(iterations, model);
  const resultsSection = document.getElementById('results');
  if (result.resultShape === 'scalar') {
    showScalarResults(result.summary);
  } else {
    showTimelineResults(result.summary);
  }
  resultsSection.classList.remove('hidden');
});
