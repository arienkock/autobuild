import { runSimulation } from "./simulation.js";
import { sumModel, npvModel } from "./model.js";
import { constant, sampled } from "./variable.js";
import { uniform, normal, triangular, pareto } from "./distributions.js";
import { computeStats, computeTimelineStats } from "./analysis.js";
import { renderNpvConeChart } from "./chart.js";

function createDemoSumModel() {
  return sumModel([
    constant(10),
    sampled(uniform(0, 5)),
    sampled(normal(2, 1)),
    constant(3),
    sampled(triangular(0, 2, 4)),
    sampled(pareto(1, 2)),
  ]);
}

function createNpvModelFromInputs(inputs) {
  const initialInvestment = constant(Number(inputs.initialInvestment.value) || 0);
  const discountRate = constant(Number(inputs.discountRate.value) || 0.1);
  const years = Math.max(1, Math.min(30, parseInt(inputs.years.value, 10) || 10));
  const cfMean = Number(inputs.cashflowMean.value) || 100;
  const cfStd = Math.max(0, Number(inputs.cashflowStd.value) || 30);
  const cashflows = Array.from({ length: years }, () => sampled(normal(cfMean, cfStd)));
  return npvModel({ initialInvestment, discountRate, cashflows });
}

function formatNumber(x) {
  return Number.isInteger(x) ? String(x) : x.toFixed(4);
}

function renderStats(container, stats) {
  container.innerHTML = "";
  const entries = [
    ["Mean", stats.mean],
    ["Median", stats.median],
    ["Std dev", stats.stdDev],
    ["Mean − 1σ", stats.band1Lower],
    ["Mean + 1σ", stats.band1Upper],
    ["Mean − 2σ", stats.band2Lower],
    ["Mean + 2σ", stats.band2Upper],
  ];
  const dl = document.createElement("dl");
  entries.forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.className = "value";
    dd.textContent = formatNumber(value);
    dl.appendChild(dt);
    dl.appendChild(dd);
  });
  container.appendChild(dl);
}

function findBreakEvenYear(medianTimeline) {
  for (let t = 0; t < medianTimeline.length; t++) {
    if (medianTimeline[t] >= 0) return t;
  }
  return null;
}

function runSumModel(iterationsInput, model, statsContainer, chartContainer) {
  const n = Math.max(100, parseInt(iterationsInput.value, 10) || 1000);
  const results = runSimulation(model, n);
  const stats = computeStats(results);
  renderStats(statsContainer, stats);
  chartContainer.innerHTML = "";
  chartContainer.classList.add("hidden");
}

function runNpvModel(iterationsInput, model, statsContainer, chartContainer, breakEvenEl) {
  const n = Math.max(100, parseInt(iterationsInput.value, 10) || 1000);
  const timelines = runSimulation(model, n);
  const timelineStats = computeTimelineStats(timelines);
  renderNpvConeChart(chartContainer, timelineStats);
  chartContainer.classList.remove("hidden");

  const breakEvenYear = findBreakEvenYear(timelineStats.median);
  if (breakEvenEl) {
    if (breakEvenYear !== null) {
      breakEvenEl.textContent = `Break-even (median): Year ${breakEvenYear}`;
      breakEvenEl.classList.remove("hidden");
    } else {
      breakEvenEl.textContent = "Break-even (median): not within horizon";
      breakEvenEl.classList.remove("hidden");
    }
  }

  statsContainer.innerHTML = "";
  statsContainer.classList.add("hidden");
}

function run(iterationsInput, modelKey, model, npvInputs, statsContainer, chartContainer, breakEvenEl) {
  if (modelKey === "sum") {
    runSumModel(iterationsInput, model, statsContainer, chartContainer);
    if (breakEvenEl) breakEvenEl.classList.add("hidden");
  } else {
    runNpvModel(iterationsInput, model, statsContainer, chartContainer, breakEvenEl);
  }
}

function toggleNpvPanel(visible) {
  const panel = document.getElementById("npv-params");
  if (panel) panel.classList.toggle("hidden", !visible);
  const chartSection = document.getElementById("chart-section");
  if (chartSection) chartSection.classList.toggle("hidden", !visible);
  const breakEvenEl = document.getElementById("break-even");
  if (breakEvenEl && !visible) breakEvenEl.classList.add("hidden");
}

const modelSelect = document.getElementById("model");
const iterationsInput = document.getElementById("iterations");
const runButton = document.getElementById("run");
const statsContainer = document.getElementById("stats");
const chartContainer = document.getElementById("chart");
const breakEvenEl = document.getElementById("break-even");
const npvInputs = {
  initialInvestment: document.getElementById("npv-initial"),
  discountRate: document.getElementById("npv-rate"),
  years: document.getElementById("npv-years"),
  cashflowMean: document.getElementById("npv-cf-mean"),
  cashflowStd: document.getElementById("npv-cf-std"),
};

const sumModelInstance = createDemoSumModel();

function getCurrentModel() {
  const key = modelSelect?.value || "sum";
  if (key === "npv") return createNpvModelFromInputs(npvInputs);
  return sumModelInstance;
}

modelSelect?.addEventListener("change", () => {
  const isNpv = modelSelect.value === "npv";
  toggleNpvPanel(isNpv);
  if (isNpv) {
    run(iterationsInput, "npv", getCurrentModel(), npvInputs, statsContainer, chartContainer, breakEvenEl);
  } else {
    run(iterationsInput, "sum", sumModelInstance, null, statsContainer, chartContainer, breakEvenEl);
  }
});

runButton?.addEventListener("click", () => {
  const key = modelSelect?.value || "sum";
  run(iterationsInput, key, getCurrentModel(), npvInputs, statsContainer, chartContainer, breakEvenEl);
});

toggleNpvPanel(modelSelect?.value === "npv");
run(iterationsInput, modelSelect?.value || "sum", getCurrentModel(), npvInputs, statsContainer, chartContainer, breakEvenEl);
