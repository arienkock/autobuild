class Model {
  constructor(evaluator) {
    this._evaluator = evaluator || defaultEvaluator;
    this._variables = [];
  }

  addVariable(variable) {
    this._variables.push(variable);
    return this;
  }

  setVariables(variables) {
    this._variables = [...variables];
    return this;
  }

  getVariables() {
    return this._variables;
  }

  evaluate() {
    return this._evaluator(this._variables);
  }
}

function defaultEvaluator(variables) {
  return variables.reduce((sum, v) => sum + v.sample(), 0);
}

export { Model, defaultEvaluator };
