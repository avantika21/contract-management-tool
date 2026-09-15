export function formatCurrency(amount, currency) {
  if (amount === null || amount === undefined) return null;
  try {
    return new Intl.NumberFormat("en-GB", {
      style: "currency",
      currency: currency || "GBP",
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${currency || ""} ${amount}`.trim();
  }
}

// Sums contract values grouped by currency (amounts in different currencies
// can't be added together) and renders each group, largest first.
export function formatValueBreakdown(contracts) {
  const totals = {};
  for (const c of contracts) {
    if (c.contract_value_amount === null || c.contract_value_amount === undefined) continue;
    const currency = c.contract_value_currency || "GBP";
    totals[currency] = (totals[currency] || 0) + Number(c.contract_value_amount);
  }
  const parts = Object.entries(totals)
    .sort((a, b) => b[1] - a[1])
    .map(([currency, amount]) => formatCurrency(amount, currency));
  return parts.length ? parts.join(" + ") : null;
}

export function daysUntil(dateStr) {
  if (!dateStr) return null;
  return Math.ceil((new Date(dateStr) - new Date()) / 86400000);
}

// The date procurement must act by to avoid an unwanted auto-renewal or a
// lapse in coverage - expiry minus the contractual notice period, not the
// expiry date itself.
export function renewalActionDate(contract) {
  if (!contract.expiry_date) return null;
  const days = contract.renewal_notice_days;
  if (!days) return contract.expiry_date;
  const d = new Date(contract.expiry_date);
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}
