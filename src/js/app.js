import { Variable } from "./variable.js";
import { Model } from "./model.js";
import { npvEvaluator } from "./npv-model.js";
import { uniform, normal, triangular, pareto } from "./distributions.js";
import { runSimulation } from "./simulation.js";
import { getSummary, getTimelineSummary } from "./statistics.js";
import { renderConeChart } from "./cone-chart.js";

const DISTRIBUTIONS = {
  constant: { label: "Constant", params: ["value"], defaults: [0] },
  uniform: { label: "Uniform", params: ["a", "b"], defaults: [0, 1] },
  normal: { label: "Normal", params: ["mean", "stdDev"], defaults: [0, 1] },
  triangular: { label: "Triangular", params: ["a", "b", "c"], defaults: [0, 1, 0.5] },
  pareto: { label: "Pareto", params: ["alpha", "xm"], defaults: [1, 1] },
  arbitrary: { label: "Arbitrary", params: ["values"], defaults: ["0,1,2"] },
};

function createVariableFromUI(type, paramValues) {
  const num = (v) => Number(v);
  switch (type) {
    case "constant":
      return Variable.constant(num(paramValues.value));
    case "uniform":
      return Variable.distribution(uniform(num(paramValues.a), num(paramValues.b)));
    case "normal":
      return Variable.distribution(normal(num(paramValues.mean), num(paramValues.stdDev)));
    case "triangular":
      return Variable.distribution(triangular(num(paramValues.a), num(paramValues.b), num(paramValues.c)));
    case "pareto":
      return Variable.distribution(pareto(num(paramValues.alpha), num(paramValues.xm)));
    case "arbitrary":
      const values = paramValues.values.split(",").map((s) => num(s.trim()));
      return Variable.arbitrary(values);
    default:
      return Variable.constant(0);
  }
}

function buildVariableRow(id) {
  const container = document.createElement("div");
  container.className = "variable-row";
  container.dataset.id = id;

  const select = document.createElement("select");
  select.dataset.param = "type";
  Object.entries(DISTRIBUTIONS).forEach(([key, { label }]) => {
    const opt = document.createElement("option");
    opt.value = key;
    opt.textContent = label;
    select.appendChild(opt);
  });

  const paramsDiv = document.createElement("div");
  paramsDiv.className = "params";

  function refreshParams() {
    paramsDiv.innerHTML = "";
    const type = select.value;
    const config = DISTRIBUTIONS[type];
    config.params.forEach((p, i) => {
      const input = document.createElement("input");
      input.dataset.param = p;
      input.placeholder = p;
      input.value = config.defaults[i];
      if (p === "value" || p === "a" || p === "b" || p === "mean" || p === "stdDev" || p === "c" || p === "alpha" || p === "xm") {
        input.type = "number";
        input.step = "any";
      }
      paramsDiv.appendChild(input);
    });
  }

  select.addEventListener("change", refreshParams);
  refreshParams();

  const removeBtn = document.createElement("button");
  removeBtn.type = "button";
  removeBtn.textContent = "Remove";

  container.appendChild(select);
  container.appendChild(paramsDiv);
  container.appendChild(removeBtn);
  return {
    container,
    getType: () => select.value,
    getParams: () => [...paramsDiv.querySelectorAll("input")].reduce((o, i) => ({ ...o, [i.dataset.param]: i.value }), {}),
    removeBtn,
  };
}

let variableId = 0;
let npvVariableId = 0;
const variableRows = new Map();
const npvVariableRows = new Map();

function addVariableRow(listId, rowsMap, addBtnId, maxRows = Infinity) {
  if (rowsMap.size >= maxRows) return;
  const id = ++variableId;
  const { container, getType, getParams, removeBtn } = buildVariableRow(id);
  rowsMap.set(id, { container, getType, getParams });
  removeBtn.addEventListener("click", () => {
    container.remove();
    rowsMap.delete(id);
  });
  document.getElementById(listId).appendChild(container);
  const addBtn = document.getElementById(addBtnId);
  if (addBtn) addBtn.disabled = rowsMap.size >= maxRows;
}

function addSumVariableRow() {
  addVariableRow("variable-list", variableRows, "add-variable");
}

function addNpvVariableRow() {
  addVariableRow("npv-variable-list", npvVariableRows, "add-npv-variable", 2);
}

function collectVariables(rowsMap = variableRows) {
  const vars = [];
  rowsMap.forEach(({ container, getType, getParams }) => {
    if (!container.parentNode) return;
    const type = getType();
    const params = getParams();
    vars.push(createVariableFromUI(type, params));
  });
  return vars;
}

function collectNpvVariables() {
  return collectVariables(npvVariableRows);
}

function displaySummary(summary) {
  const rows = [
    ["Mean", summary.mean],
    ["Median", summary.median],
    ["Std Dev", summary.stdDev],
    ["Mean − 2σ", summary.minus2StdDev],
    ["Mean − 1σ", summary.minus1StdDev],
    ["Mean + 1σ", summary.plus1StdDev],
    ["Mean + 2σ", summary.plus2StdDev],
  ];
  const tbody = document.getElementById("results-body");
  tbody.innerHTML = "";
  rows.forEach(([label, value]) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${label}</td><td>${Number(value).toFixed(4)}</td>`;
    tbody.appendChild(tr);
  });
  document.getElementById("results-sum").hidden = false;
  document.getElementById("results-npv").hidden = true;
  document.getElementById("results").hidden = false;
}

function displayTimelineSummary(summary) {
  document.getElementById("results-sum").hidden = true;
  document.getElementById("results-npv").hidden = false;
  const container = document.getElementById("cone-chart-container");
  renderConeChart(container, summary);
  document.getElementById("results").hidden = false;
}

function onModelTypeChange() {
  const modelType = document.getElementById("model-type").value;
  document.getElementById("section-sum").hidden = modelType === "npv";
  document.getElementById("section-npv").hidden = modelType !== "npv";
}

document.getElementById("model-type").addEventListener("change", onModelTypeChange);

document.getElementById("add-variable").addEventListener("click", addSumVariableRow);
document.getElementById("add-npv-variable").addEventListener("click", addNpvVariableRow);

document.getElementById("run").addEventListener("click", () => {
  const iterations = parseInt(document.getElementById("iterations").value, 10) || 10000;
  const modelType = document.getElementById("model-type").value;

  if (modelType === "npv") {
    const initialInvestment = Number(document.getElementById("npv-initial").value) || 0;
    const years = Math.max(1, Math.min(50, parseInt(document.getElementById("npv-years").value, 10) || 10));
    const variables = collectNpvVariables();
    if (variables.length < 2) {
      while (npvVariableRows.size < 2) addNpvVariableRow();
      return;
    }
    const evaluator = npvEvaluator(initialInvestment, years);
    const model = new Model(evaluator).setVariables(variables.slice(0, 2));
    const results = runSimulation(iterations, model);
    const summary = getTimelineSummary(results);
    displayTimelineSummary(summary);
    return;
  }

  const variables = collectVariables();
  if (variables.length === 0) {
    addSumVariableRow();
    return;
  }
  const model = new Model().setVariables(variables);
  const results = runSimulation(iterations, model);
  const summary = getSummary(results);
  displaySummary(summary);
});

onModelTypeChange();
addSumVariableRow();
addNpvVariableRow();
addNpvVariableRow();
