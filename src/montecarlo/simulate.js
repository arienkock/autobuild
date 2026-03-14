export function simulate(model, iterations) {
  return Array.from({ length: iterations }, () => model.evaluate())
}
