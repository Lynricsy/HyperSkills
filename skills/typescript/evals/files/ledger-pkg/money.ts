export type Currency = "EUR" | "USD" | "GBP";

export function toMinorUnits(amount: number, currency: Currency) {
  const digits = currency === "GBP" || currency === "EUR" || currency === "USD" ? 2 : 0;
  return Math.round(amount * 10 ** digits);
}

function readCurrency(raw: string | undefined): Currency {
  return raw === "USD" || raw === "GBP" ? raw : "EUR";
}

export const defaultCurrency = readCurrency(process.env.LEDGER_CURRENCY);
