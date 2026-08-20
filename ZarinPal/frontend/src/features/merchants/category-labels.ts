import type { Locale } from "@/app/i18n";

const englishCategories: Record<string, string> = {
  "48160000": "Computer network and internet services",
  "48160002": "Internet service provider",
  "56610001": "Bags and footwear retailer",
  "59770001": "Cosmetics and personal care retailer",
  "82410000": "Virtual education centers",
};

export function categoryLabel(
  category: { category_id: string; title_fa: string },
  locale: Locale,
) {
  if (locale === "fa") return category.title_fa;
  return englishCategories[category.category_id] ?? category.category_id;
}

export const categoryOptions = [
  "48160000",
  "48160002",
  "56610001",
  "59770001",
  "82410000",
] as const;

export function categoryOptionLabel(categoryId: string, locale: Locale) {
  if (locale === "en") return englishCategories[categoryId] ?? categoryId;
  const persianCategories: Record<string, string> = {
    "48160000": "خدمات شبکه‌های کامپیوتری و اینترنت",
    "48160002": "ارائه دهنده خدمات اینترنت",
    "56610001": "کیف و کفش فروشی",
    "59770001": "فروشگاه لوازم آرایشی و بهداشتی",
    "82410000": "مراکز آموزشی مجازی",
  };
  return persianCategories[categoryId] ?? categoryId;
}
