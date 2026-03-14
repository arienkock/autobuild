class Variable {
  constructor(sampler) {
    this._sampler = sampler;
  }

  static constant(value) {
    return new Variable(() => value);
  }

  static distribution(sampler) {
    return new Variable(sampler);
  }

  static arbitrary(samplerOrValues) {
    if (typeof samplerOrValues === "function") {
      return new Variable(samplerOrValues);
    }
    const values = Array.isArray(samplerOrValues) ? samplerOrValues : [samplerOrValues];
    return new Variable(() => values[Math.floor(Math.random() * values.length)]);
  }

  sample() {
    return this._sampler();
  }
}

export { Variable };
