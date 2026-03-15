export function runSimulation(model, iterations) {
  const results = [];
  for (let i = 0; i < iterations; i++) {
    results.push(model.evaluate());
  }
  return results;
}
