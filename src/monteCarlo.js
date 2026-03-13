export function run(iterations, model, random = Math.random) {
  const results = [];
  for (let i = 0; i < iterations; i++) {
    results.push(model.run(random));
  }
  return results;
}
