import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";
import { AppProviders } from "@/app/providers";
import {
  RequireAuthentication,
  RequireMerchant,
} from "@/features/auth/components/route-guards";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function renderGuard(session: object) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(session), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
  return render(
    <AppProviders>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/login" element={<div>login route</div>} />
          <Route path="/merchants" element={<div>merchant route</div>} />
          <Route element={<RequireAuthentication />}>
            <Route element={<RequireMerchant />}>
              <Route path="/dashboard" element={<div>dashboard route</div>} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>
    </AppProviders>,
  );
}

test("redirects an unauthenticated dashboard visit to login", async () => {
  renderGuard({ authenticated: false, selected_merchant: null });
  expect(await screen.findByText("login route")).toBeVisible();
});

test("redirects an authenticated user without merchant context to selection", async () => {
  renderGuard({ authenticated: true, selected_merchant: null });
  expect(await screen.findByText("merchant route")).toBeVisible();
});

test("allows the dashboard after a merchant is selected", async () => {
  renderGuard({
    authenticated: true,
    selected_merchant: { merchant_key: "M145", categories: [] },
  });
  expect(await screen.findByText("dashboard route")).toBeVisible();
});
