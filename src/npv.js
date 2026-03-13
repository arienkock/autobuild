export function npv(cashFlows, discountRate) {
  if (!Array.isArray(cashFlows)) {
    throw new TypeError("cashFlows must be an array");
  }
  if (!Number.isFinite(discountRate)) {
    throw new TypeError("discountRate must be finite");
  }
  let total = 0;
  const r = 1 + discountRate;
  for (let t = 0; t < cashFlows.length; t += 1) {
    const cf = cashFlows[t];
    if (!Number.isFinite(cf)) {
      throw new TypeError("cashFlows must contain only finite numbers");
    }
    total += cf / r ** t;
  }
  return total;
}

export function presentValue(amount, discountRate, period) {
  if (!Number.isFinite(amount)) {
    throw new TypeError("amount must be finite");
  }
  if (!Number.isFinite(discountRate)) {
    throw new TypeError("discountRate must be finite");
  }
  if (!Number.isInteger(period) || period < 0) {
    throw new TypeError("period must be a non-negative integer");
  }
  return amount / (1 + discountRate) ** period;
}
