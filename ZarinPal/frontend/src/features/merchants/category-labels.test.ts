import { expect, test } from "vitest";
import { categoryLabel } from "@/features/merchants/category-labels";

const category = {
  category_id: "48160002",
  title_fa: "ارائه دهنده خدمات اینترنت",
};

test("uses the source title in Persian and curated translation in English", () => {
  expect(categoryLabel(category, "fa")).toBe("ارائه دهنده خدمات اینترنت");
  expect(categoryLabel(category, "en")).toBe("Internet service provider");
});
