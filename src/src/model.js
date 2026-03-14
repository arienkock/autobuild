export class SumModel {
  constructor(variables) {
    this.variables = variables;
  }

  run() {
    return this.variables.reduce((sum, variable) => sum + variable.sample(), 0);
  }
}
