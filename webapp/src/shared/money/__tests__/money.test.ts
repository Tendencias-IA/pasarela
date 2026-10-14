import { describe, expect, it } from "vitest";

import { RECHARGE_MAX, RECHARGE_MIN, formatCOP, isWithinRange, parseAmountInput } from "..";

describe("parseAmountInput (RNF-04.3)", () => {
  it.each([
    ["50000", "50000.00"],
    ["50.000", "50000.00"],
    ["50000,50", "50000.50"],
    ["50000.5", "50000.50"],
    [" 5.000.000 ", "5000000.00"],
    ["1,5", "1.50"],
    ["1.234,5", "1234.50"],
  ])("normaliza %s a %s", (raw, expected) => {
    expect(parseAmountInput(raw)).toBe(expected);
  });

  it.each([
    "",
    "abc",
    "-1",
    "1.234.5",
    "1.2345",
    "0",
    "0,00",
    "12345678901234",
    "5e3",
    "12.34.567",
  ])("rechaza %s", (raw) => {
    expect(parseAmountInput(raw)).toBeNull();
  });
});

describe("isWithinRange (HU-08 CA-1, CA-2)", () => {
  it.each([
    ["4999.99", false],
    ["5000.00", true],
    ["5000000.00", true],
    ["5000000.01", false],
  ])("%s dentro del rango de recarga: %s", (amount, expected) => {
    expect(isWithinRange(amount, RECHARGE_MIN, RECHARGE_MAX)).toBe(expected);
  });
});

describe("formatCOP", () => {
  it("agrupa miles con punto y decimales con coma", () => {
    expect(formatCOP("50000.00")).toBe("$ 50.000,00");
    expect(formatCOP("5000000.50")).toBe("$ 5.000.000,50");
    expect(formatCOP("5.00")).toBe("$ 5,00");
  });
});
