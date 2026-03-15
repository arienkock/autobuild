export function constant(value) {
  return {
    sample() {
      return value;
    },
  };
}

export function sampled(sampler) {
  return {
    sample() {
      return sampler();
    },
  };
}

export function arbitrary(value) {
  return {
    sample() {
      return value;
    },
  };
}
