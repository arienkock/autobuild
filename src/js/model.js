export function sumModel(variables) {
  return {
    evaluate() {
      return variables.reduce((sum, v) => sum + v.sample(), 0);
    },
  };
}
