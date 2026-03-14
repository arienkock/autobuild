export class Constant {
  constructor(value) {
    this.value = value;
  }

  sample() {
    return this.value;
  }
}

export class Normal {
  constructor(mean, stdDev) {
    this.mean = mean;
    this.stdDev = stdDev;
  }

  sample() {
    let u1 = Math.random();
    let u2 = Math.random();
    let z0 = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
    return z0 * this.stdDev + this.mean;
  }
}

export class Uniform {
  constructor(min, max) {
    this.min = min;
    this.max = max;
  }

  sample() {
    return Math.random() * (this.max - this.min) + this.min;
  }
}
