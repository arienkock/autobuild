const tests = [];

export function test(name, fn) {
  tests.push({ name, fn });
}

export function assertApproxEqual(actual, expected, tolerance, message) {
  const error = Math.abs(actual - expected);
  if (!(error <= tolerance)) {
    throw new Error(
      message ||
        `Expected ${expected} ± ${tolerance}, got ${actual} (error ${error})`
    );
  }
}

export function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(message || `Expected ${expected}, got ${actual}`);
  }
}

function logResult(name, passed, error) {
  const line = document.createElement("div");
  line.textContent = passed ? `✓ ${name}` : `✗ ${name}: ${error.message}`;
  line.style.fontFamily =
    'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace';
  line.style.fontSize = "13px";
  line.style.color = passed ? "#22c55e" : "#f97373";
  document.getElementById("results").appendChild(line);
}

export async function runTests() {
  const container = document.getElementById("results");
  container.innerHTML = "";
  let passed = 0;
  for (const { name, fn } of tests) {
    try {
      await fn();
      logResult(name, true);
      passed += 1;
    } catch (e) {
      logResult(name, false, e instanceof Error ? e : new Error(String(e)));
    }
  }
  const summary = document.createElement("div");
  summary.style.marginTop = "8px";
  summary.style.fontWeight = "600";
  summary.textContent = `Passed ${passed} / ${tests.length}`;
  container.appendChild(summary);
}

runTests();

