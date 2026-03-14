export class Variable {
  sample() {
    throw new Error('Variable.sample() not implemented')
  }
}

export class Constant extends Variable {
  constructor(value) {
    super()
    this.value = value
  }
  sample() {
    return this.value
  }
}

export class Arbitrary extends Variable {
  constructor(fn) {
    super()
    this.fn = fn
  }
  sample() {
    return this.fn()
  }
}

export class Uniform extends Variable {
  constructor(min, max) {
    super()
    this.min = min
    this.max = max
  }
  sample() {
    return this.min + Math.random() * (this.max - this.min)
  }
}

export class Normal extends Variable {
  constructor(mean, stddev) {
    super()
    this.mean = mean
    this.stddev = stddev
  }
  sample() {
    const u1 = Math.random()
    const u2 = Math.random()
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2)
    return this.mean + z * this.stddev
  }
}

export class Triangular extends Variable {
  constructor(min, mode, max) {
    super()
    this.min = min
    this.mode = mode
    this.max = max
  }
  sample() {
    const u = Math.random()
    const fc = (this.mode - this.min) / (this.max - this.min)
    if (u < fc) {
      return this.min + Math.sqrt(u * (this.max - this.min) * (this.mode - this.min))
    }
    return this.max - Math.sqrt((1 - u) * (this.max - this.min) * (this.max - this.mode))
  }
}

export class Pareto extends Variable {
  constructor(scale, shape) {
    super()
    this.scale = scale
    this.shape = shape
  }
  sample() {
    return this.scale / Math.pow(1 - Math.random(), 1 / this.shape)
  }
}
