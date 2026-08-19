import { expect, test } from "@playwright/test";

test("frontend routes and reaches FastAPI", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: /Start building the product/ }),
  ).toBeVisible();

  await page.goto("/example");
  await expect(page.getByText("API status: ok")).toBeVisible();

  const health = await page.request.get("/api/health");
  expect(health.ok()).toBe(true);
  await expect(health.json()).resolves.toEqual({ status: "ok" });
});
