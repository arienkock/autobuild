export class Model {
  constructor(variables) {
    this.variables = variables
  }

  evaluate() {
    return this.variables.reduce((sum, v) => sum + v.sample(), 0)
  }
}
