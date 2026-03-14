export class Simulation {
  run(iterations, model) {
    const results = [];
    for (let i = 0; i < iterations; i++) {
      results.push(model.run());
    }
    return results;
  }
}
