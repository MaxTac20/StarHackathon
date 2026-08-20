import {
  addMonths as addJalaliMonths,
  format as formatJalali,
  startOfMonth as startOfJalaliMonth,
} from "date-fns-jalali";
import type { Locale } from "@/app/i18n";

function parseLocalDate(value: string) {
  return new Date(`${value.slice(0, 10)}T00:00:00`);
}

export function toIsoLocalDate(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatDashboardDate(value: string, locale: Locale) {
  const parsed = new Date(value.includes("T") ? value : `${value}T00:00:00`);
  return locale === "fa"
    ? formatJalali(parsed, "yyyy/MM/dd")
    : new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(parsed);
}

export function calendarMonthRange(value: Date, locale: Locale) {
  const start =
    locale === "fa"
      ? startOfJalaliMonth(value)
      : new Date(value.getFullYear(), value.getMonth(), 1);
  const end =
    locale === "fa"
      ? addJalaliMonths(start, 1)
      : new Date(start.getFullYear(), start.getMonth() + 1, 1);
  return { start: toIsoLocalDate(start), end: toIsoLocalDate(end) };
}

export function shiftCalendarMonth(
  value: string,
  amount: number,
  locale: Locale,
) {
  const current = parseLocalDate(value);
  const shifted =
    locale === "fa"
      ? addJalaliMonths(current, amount)
      : new Date(current.getFullYear(), current.getMonth() + amount, 1);
  return calendarMonthRange(shifted, locale);
}

export function previousEqualRange(start: string, end: string) {
  const startDate = parseLocalDate(start);
  const endDate = parseLocalDate(end);
  const duration = endDate.getTime() - startDate.getTime();
  return {
    start: toIsoLocalDate(new Date(startDate.getTime() - duration)),
    end: start,
  };
}

export function inclusiveRangeEnd(end: string) {
  const parsed = parseLocalDate(end);
  parsed.setDate(parsed.getDate() - 1);
  return toIsoLocalDate(parsed);
}

export function exclusiveRangeEnd(endInclusive: string) {
  const parsed = parseLocalDate(endInclusive);
  parsed.setDate(parsed.getDate() + 1);
  return toIsoLocalDate(parsed);
}

export function buildDrilldownQuery(scopeQuery: string, extra: string) {
  const params = new URLSearchParams(scopeQuery.replace(/^\?/, ""));
  new URLSearchParams(extra).forEach((value, key) => {
    params.set(key, value);
  });
  return params.toString();
}
