import { runSimulation } from "./simulation.js";
import { sumModel } from "./model.js";
import { constant, sampled, arbitrary } from "./variable.js";
import { uniform, normal, triangular, pareto } from "./distributions.js";
import { computeStats } from "./analysis.js";

function createDemoModel() {
  return sumModel([
    constant(10),
    sampled(uniform(0, 5)),
    sampled(normal(2, 1)),
    arbitrary(3),
    sampled(triangular(0, 2, 4)),
    sampled(pareto(1, 2)),
  ]);
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

function run(iterationsInput, model, statsContainer) {
  const n = Math.max(100, parseInt(iterationsInput.value, 10) || 1000);
  const results = runSimulation(model, n);
  const stats = computeStats(results);
  renderStats(statsContainer, stats);
}

const iterationsInput = document.getElementById("iterations");
const runButton = document.getElementById("run");
const statsContainer = document.getElementById("stats");
const model = createDemoModel();

runButton.addEventListener("click", () => run(iterationsInput, model, statsContainer));
run(iterationsInput, model, statsContainer);
