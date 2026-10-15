import { defaultCurrency, toMinorUnits, type Currency } from "#/money.js";

export interface Entry {
  account: string;
  minor: number;
  currency: Currency;
}

export function postEntry(account: string, amount: number): Entry {
  return { account, minor: toMinorUnits(amount, defaultCurrency), currency: defaultCurrency };
}

console.log(JSON.stringify(postEntry("cash", 12.5)));
