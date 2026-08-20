import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";
import { ExamplePage } from "@/pages/example-page";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
});

test("renders the backend health response", async () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <ExamplePage />
    </QueryClientProvider>,
  );
  expect(await screen.findByText("API status: ok")).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledWith("/api/health", expect.any(Object));
});
