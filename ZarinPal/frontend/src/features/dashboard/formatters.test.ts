import { describe, expect, it } from "vitest";
import {
  buildDrilldownQuery,
  calendarMonthRange,
  exclusiveRangeEnd,
  formatDashboardDate,
  inclusiveRangeEnd,
  previousEqualRange,
  shiftCalendarMonth,
} from "@/features/dashboard/formatters";

describe("dashboard presentation helpers", () => {
  it("uses Jalali dates in Persian and Gregorian dates in English", () => {
    expect(formatDashboardDate("2026-03-21", "fa")).toBe("1405/01/01");
    expect(formatDashboardDate("2026-03-21", "en")).toContain("2026");
  });

  it("keeps dashboard scope when adding a reproducible drill-down", () => {
    const query = buildDrilldownQuery(
      "?start=2026-05-01&end=2026-06-01&terminal_key=T1",
      "status=Failed&no_attempt=true",
    );
    const params = new URLSearchParams(query);
    expect(Object.fromEntries(params)).toEqual({
      start: "2026-05-01",
      end: "2026-06-01",
      terminal_key: "T1",
      status: "Failed",
      no_attempt: "true",
    });
  });

  it("builds and moves Gregorian calendar-month ranges", () => {
    expect(calendarMonthRange(new Date(2026, 4, 18), "en")).toEqual({
      start: "2026-05-01",
      end: "2026-06-01",
    });
    expect(shiftCalendarMonth("2026-05-01", -1, "en")).toEqual({
      start: "2026-04-01",
      end: "2026-05-01",
    });
  });

  it("uses Jalali month boundaries in Persian", () => {
    expect(calendarMonthRange(new Date(2026, 2, 25), "fa")).toEqual({
      start: "2026-03-21",
      end: "2026-04-21",
    });
  });

  it("describes the immediately preceding equal-length period", () => {
    expect(previousEqualRange("2026-05-10", "2026-05-25")).toEqual({
      start: "2026-04-25",
      end: "2026-05-10",
    });
    expect(inclusiveRangeEnd("2026-05-25")).toBe("2026-05-24");
    expect(exclusiveRangeEnd("2026-05-24")).toBe("2026-05-25");
  });
});
