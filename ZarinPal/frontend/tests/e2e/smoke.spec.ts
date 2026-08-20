import { expect, test } from "@playwright/test";

test("login, merchant selection, switching, and logout", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: "ورود به نسخه نمایشی" }),
  ).toBeVisible();
  await expect(page.getByText("CHANGE_ME")).toBeVisible();

  await page
    .getByRole("textbox", { name: "رمز عبور", exact: true })
    .fill(process.env.E2E_APP_PASSWORD ?? "CHANGE_ME");
  await page.getByRole("button", { name: "ورود" }).click();
  await expect(page).toHaveURL(/\/merchants$/);
  await expect(
    page.getByRole("heading", { name: "انتخاب پذیرنده" }),
  ).toBeVisible();

  await page
    .getByRole("button", { name: "انتخاب", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(
    page.getByRole("heading", {
      name: "از تلاش‌های پرداخت تا تصمیم عملیاتی",
    }),
  ).toBeVisible();

  await page.getByRole("link", { name: "تغییر پذیرنده" }).click();
  await expect(page).toHaveURL(/\/merchants$/);
  await page.getByRole("button", { name: "خروج" }).click();
  await expect(page).toHaveURL(/\/login$/);

  const health = await page.request.get("/api/health");
  expect(health.ok()).toBe(true);
  await expect(health.json()).resolves.toEqual({ status: "ok" });
});
