import { runMonteCarlo } from "./simulation.js";

function parseNumber(input) {
  const value = Number(input);
  if (!Number.isFinite(value)) {
    return null;
  }
  return value;
}

function formatCurrency(amount) {
  if (!Number.isFinite(amount)) {
    return "–";
  }
  const abs = Math.abs(amount);
  const rounded = Math.round(abs);
  const parts = rounded.toString().split("");
  const out = [];
  for (let i = 0; i < parts.length; i += 1) {
    const fromEnd = parts.length - i;
    out.push(parts[i]);
    if (fromEnd > 1 && fromEnd % 3 === 1) {
      out.push(",");
    }
  }
  const sign = amount < 0 ? "-" : "";
  return `${sign}$${out.join("")}`;
}

function formatPercent(prob) {
  if (!Number.isFinite(prob)) {
    return "–";
  }
  return `${(prob * 100).toFixed(1)}%`;
}

function attach() {
  const form = document.getElementById("npv-form");
  const error = document.getElementById("error");
  const results = document.getElementById("results");
  const meanNpv = document.getElementById("meanNpv");
  const stdNpv = document.getElementById("stdNpv");
  const probPositive = document.getElementById("probPositive");
  const p5 = document.getElementById("p5");
  const p50 = document.getElementById("p50");
  const p95 = document.getElementById("p95");

  if (!form) {
    return;
  }

  form.addEventListener("submit", (evt) => {
    evt.preventDefault();
    if (error) {
      error.textContent = "";
    }

    const initialInvestmentInput = document.getElementById("initialInvestment");
    const yearsInput = document.getElementById("years");
    const meanCashFlowInput = document.getElementById("meanCashFlow");
    const stdCashFlowInput = document.getElementById("stdCashFlow");
    const discountRateInput = document.getElementById("discountRate");
    const iterationsInput = document.getElementById("iterations");

    const initialInvestment = parseNumber(initialInvestmentInput && initialInvestmentInput.value);
    const years = parseNumber(yearsInput && yearsInput.value);
    const meanCashFlow = parseNumber(meanCashFlowInput && meanCashFlowInput.value);
    const stdCashFlow = parseNumber(stdCashFlowInput && stdCashFlowInput.value);
    const discountRatePercent = parseNumber(discountRateInput && discountRateInput.value);
    const iterations = parseNumber(iterationsInput && iterationsInput.value);

    if (
      initialInvestment === null ||
      years === null ||
      meanCashFlow === null ||
      stdCashFlow === null ||
      discountRatePercent === null ||
      iterations === null
    ) {
      if (error) {
        error.textContent = "All inputs must be valid numbers.";
      }
      return;
    }

    if (!Number.isInteger(years) || years <= 0) {
      if (error) {
        error.textContent = "Years must be a positive integer.";
      }
      return;
    }

    if (!Number.isInteger(iterations) || iterations <= 0) {
      if (error) {
        error.textContent = "Iterations must be a positive integer.";
      }
      return;
    }

    if (stdCashFlow < 0) {
      if (error) {
        error.textContent = "Standard deviation must be non-negative.";
      }
      return;
    }

    const discountRate = discountRatePercent / 100;

    let result;
    try {
      result = runMonteCarlo({
        initialInvestment,
        annualCashFlowMean: meanCashFlow,
        annualCashFlowStdDev: stdCashFlow,
        years,
        discountRate,
        iterations,
      });
    } catch (e) {
      if (error) {
        error.textContent = "Simulation error.";
      }
      return;
    }

    if (meanNpv) {
      meanNpv.textContent = formatCurrency(result.meanNpv);
    }
    if (stdNpv) {
      stdNpv.textContent = formatCurrency(result.stdNpv);
    }
    if (probPositive) {
      probPositive.textContent = formatPercent(result.probPositive);
    }
    if (p5) {
      p5.textContent = formatCurrency(result.p5);
    }
    if (p50) {
      p50.textContent = formatCurrency(result.p50);
    }
    if (p95) {
      p95.textContent = formatCurrency(result.p95);
    }
    if (results) {
      results.hidden = false;
    }
  });
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attach);
  } else {
    attach();
  }
}
