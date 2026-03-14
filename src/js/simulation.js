function runSimulation(iterations, model) {
  const results = [];
  for (let i = 0; i < iterations; i++) {
    results.push(model.evaluate());
  }
  return results;
}

export { runSimulation };
