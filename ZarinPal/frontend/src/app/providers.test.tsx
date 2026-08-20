import { Button } from "@mui/material";
import { DatePicker } from "@mui/x-date-pickers";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import dayjs from "dayjs";
import { beforeEach, describe, expect, it } from "vitest";
import { useLocale } from "@/app/i18n";
import { AppProviders } from "@/app/providers";

function LocaleSwitchProbe() {
  const { locale, setLocale } = useLocale();
  return (
    <>
      <Button onClick={() => setLocale(locale === "en" ? "fa" : "en")}>
        switch locale
      </Button>
      {locale === "fa" ? (
        <DatePicker
          label="date"
          format="yyyy/MM/dd"
          value={new Date("2026-08-20T00:00:00")}
        />
      ) : (
        <DatePicker
          label="date"
          format="MM/DD/YYYY"
          value={dayjs("2026-08-20")}
        />
      )}
    </>
  );
}

describe("AppProviders", () => {
  beforeEach(() => window.localStorage.setItem("ui-locale", "en"));

  it("remounts date pickers when changing calendar adapters", async () => {
    render(
      <AppProviders>
        <LocaleSwitchProbe />
      </AppProviders>,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "switch locale" }),
    );

    expect(document.documentElement).toHaveAttribute("dir", "rtl");
    const input = screen
      .getAllByLabelText("date")
      .find((element) => element instanceof HTMLInputElement);
    expect(input).toHaveValue("1405/05/29");
  });
});
