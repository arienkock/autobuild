import { createTriangularSampler, runNpvSimulation } from "./npvCore.js";

const periodCountInput = document.getElementById("periodCount");
const discountRateInput = document.getElementById("discountRate");
const iterationsInput = document.getElementById("iterations");
const successThresholdInput = document.getElementById("successThreshold");
const cashflowBody = document.getElementById("cashflowBody");
const runButton = document.getElementById("runButton");
const errorEl = document.getElementById("error");
const meanNpvEl = document.getElementById("meanNpv");
const probSuccessEl = document.getElementById("probSuccess");
const p5El = document.getElementById("p5");
const p95El = document.getElementById("p95");

function formatCurrency(value) {
  if (!Number.isFinite(value)) {
    return "–";
  }
  const rounded = Math.round(value);
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(rounded);
}

function formatPercent(value) {
  if (!Number.isFinite(value)) {
    return "–";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function parseNumber(input) {
  const value = parseFloat(input.value);
  return Number.isFinite(value) ? value : NaN;
}

function buildCashflowRows(count) {
  cashflowBody.innerHTML = "";
  const n = Math.max(1, Math.min(40, count));
  for (let year = 0; year < n; year++) {
    const row = document.createElement("tr");

    const yearCell = document.createElement("td");
    yearCell.textContent = String(year);
    row.appendChild(yearCell);

    const minCell = document.createElement("td");
    const minInput = document.createElement("input");
    minInput.type = "number";
    minInput.className = "cashflow-input";
    minInput.value = year === 0 ? "-100000" : "30000";
    minCell.appendChild(minInput);
    row.appendChild(minCell);

    const modeCell = document.createElement("td");
    const modeInput = document.createElement("input");
    modeInput.type = "number";
    modeInput.className = "cashflow-input";
    modeInput.value = year === 0 ? "-90000" : "50000";
    modeCell.appendChild(modeInput);
    row.appendChild(modeCell);

    const maxCell = document.createElement("td");
    const maxInput = document.createElement("input");
    maxInput.type = "number";
    maxInput.className = "cashflow-input";
    maxInput.value = year === 0 ? "-80000" : "70000";
    maxCell.appendChild(maxInput);
    row.appendChild(maxCell);

    cashflowBody.appendChild(row);
  }
}

function collectSamplers() {
  const rows = Array.from(cashflowBody.querySelectorAll("tr"));
  const samplers = [];
  for (const row of rows) {
    const inputs = row.querySelectorAll("input");
    if (inputs.length !== 3) {
      throw new Error("Unexpected cash flow row structure");
    }
    const min = parseFloat(inputs[0].value);
    const mode = parseFloat(inputs[1].value);
    const max = parseFloat(inputs[2].value);
    if (!Number.isFinite(min) || !Number.isFinite(mode) || !Number.isFinite(max)) {
      throw new Error("All cash flow values must be numbers");
    }
    samplers.push(createTriangularSampler(min, mode, max));
  }
  return samplers;
}

function run() {
  errorEl.textContent = "";
  runButton.disabled = true;
  try {
    const discountRatePercent = parseNumber(discountRateInput);
    const iterations = parseNumber(iterationsInput);
    const threshold = parseNumber(successThresholdInput);
    if (!Number.isFinite(discountRatePercent)) {
      throw new Error("Discount rate is required");
    }
    if (!Number.isFinite(iterations) || iterations <= 0) {
      throw new Error("Iterations must be a positive number");
    }
    if (!Number.isFinite(threshold)) {
      throw new Error("Success threshold is required");
    }
    const discountRate = discountRatePercent / 100;
    const samplers = collectSamplers();
    const result = runNpvSimulation({
      periods: samplers,
      discountRate,
      iterations: Math.floor(iterations),
    });
    const probability = result.probability((npv) => npv >= threshold);
    meanNpvEl.textContent = formatCurrency(result.mean);
    probSuccessEl.textContent = formatPercent(probability);
    p5El.textContent = formatCurrency(result.percentile(0.05));
    p95El.textContent = formatCurrency(result.percentile(0.95));
  } catch (e) {
    errorEl.textContent = e instanceof Error ? e.message : String(e);
  } finally {
    runButton.disabled = false;
  }
}

runButton.addEventListener("click", () => {
  run();
});

periodCountInput.addEventListener("change", () => {
  const value = parseInt(periodCountInput.value, 10);
  const count = Number.isInteger(value) ? value : 1;
  buildCashflowRows(count);
});

buildCashflowRows(parseInt(periodCountInput.value, 10) || 5);

