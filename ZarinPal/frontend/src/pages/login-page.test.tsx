import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router";
import { AppProviders } from "@/app/providers";
import { LoginPage } from "@/pages/login-page";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("shows the documented default and submits the shared password", async () => {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(
      JSON.stringify({ authenticated: true, selected_merchant: null }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      },
    ),
  );
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();

  render(
    <AppProviders>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </AppProviders>,
  );

  expect(screen.getByText("CHANGE_ME")).toBeVisible();
  expect(screen.getByText("APP_PASSWORD")).toBeVisible();
  await user.type(screen.getByLabelText("رمز عبور"), "CHANGE_ME");
  await user.click(screen.getByRole("button", { name: "ورود" }));

  expect(fetchMock).toHaveBeenCalledWith(
    "/api/auth/login",
    expect.objectContaining({ method: "POST", credentials: "same-origin" }),
  );
});

test("renders a localized error for invalid credentials", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { message: "Invalid password" } }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
  const user = userEvent.setup();
  render(
    <AppProviders>
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    </AppProviders>,
  );

  await user.type(screen.getByLabelText("رمز عبور"), "wrong");
  await user.click(screen.getByRole("button", { name: "ورود" }));
  expect(await screen.findByText(/رمز عبور صحیح نیست/)).toBeVisible();
});
