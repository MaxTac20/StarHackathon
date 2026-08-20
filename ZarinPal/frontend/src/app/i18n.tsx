import type { PropsWithChildren } from "react";
import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type Locale = "fa" | "en";

const messages = {
  fa: {
    productName: "دیدبان پرداخت",
    navOverview: "نمای کلی",
    navSystem: "وضعیت سامانه",
    language: "زبان",
    appearance: "ظاهر",
    light: "روشن",
    dark: "تیره",
    system: "سیستم",
    pageEyebrow: "تحلیل عملکرد درگاه پرداخت",
    pageTitle: "از تلاش‌های پرداخت تا تصمیم عملیاتی",
    pageDescription:
      "نمایی دقیق و قابل ردیابی از سلامت پرداخت، روندها و علت خطاها برای هر پذیرنده.",
    foundationStatus: "وضعیت راه‌اندازی",
    foundationMessage:
      "زیرساخت رابط کاربری آماده است. شاخص‌ها پس از تأیید واحد پول، منطقه زمانی و معنای وضعیت‌ها به داده واقعی متصل می‌شوند.",
    primaryAction: "بررسی وضعیت سامانه",
    health: "سلامت فعلی",
    kpis: "شاخص‌های اصلی",
    trends: "روندها و تغییرات",
    healthDescription: "مشاهده سریع دسترس‌پذیری و تازگی داده",
    kpisDescription: "تعریف شفاف صورت و مخرج هر شاخص",
    trendsDescription: "حرکت از تغییر مهم به تراکنش‌های مؤثر",
    systemTitle: "وضعیت ارتباط با API",
    systemDescription:
      "این صفحه مسیر یکپارچه React، FastAPI و API هم‌مبدأ را بررسی می‌کند.",
    checking: "در حال بررسی…",
    unavailable: "سرویس در دسترس نیست",
    apiStatus: "وضعیت API",
    refresh: "به‌روزرسانی",
    error404: "۴۰۴",
    notFound: "صفحه پیدا نشد",
    returnHome: "بازگشت به نمای کلی",
  },
  en: {
    productName: "Payment Watch",
    navOverview: "Overview",
    navSystem: "System status",
    language: "Language",
    appearance: "Appearance",
    light: "Light",
    dark: "Dark",
    system: "System",
    pageEyebrow: "Payment gateway analytics",
    pageTitle: "From payment attempts to operational decisions",
    pageDescription:
      "A precise, traceable view of payment health, trends, and failure causes for each merchant.",
    foundationStatus: "Implementation status",
    foundationMessage:
      "The UI foundation is ready. Metrics will connect to real data after currency, timezone, and status semantics are confirmed.",
    primaryAction: "Check system status",
    health: "Current health",
    kpis: "Primary KPIs",
    trends: "Trends and changes",
    healthDescription:
      "See service availability and data freshness at a glance",
    kpisDescription: "Explain every metric numerator and denominator",
    trendsDescription: "Move from a notable change to its contributing records",
    systemTitle: "API connection status",
    systemDescription:
      "This page verifies the integrated React, FastAPI, and same-origin API path.",
    checking: "Checking…",
    unavailable: "Service unavailable",
    apiStatus: "API status",
    refresh: "Refresh",
    error404: "404",
    notFound: "Page not found",
    returnHome: "Return to overview",
  },
} as const;

type Messages = (typeof messages)[Locale];

interface LocaleContextValue {
  locale: Locale;
  direction: "rtl" | "ltr";
  messages: Messages;
  setLocale: (locale: Locale) => void;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

export function LocaleProvider({ children }: PropsWithChildren) {
  const [locale, setLocale] = useState<Locale>(() => {
    const stored = window.localStorage.getItem("ui-locale");
    return stored === "en" ? "en" : "fa";
  });
  const direction: "rtl" | "ltr" = locale === "fa" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.lang = locale === "fa" ? "fa" : "en";
    document.documentElement.dir = direction;
    window.localStorage.setItem("ui-locale", locale);
  }, [direction, locale]);

  const value = useMemo(
    () => ({ locale, direction, messages: messages[locale], setLocale }),
    [direction, locale],
  );

  return (
    <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
  );
}

export function useLocale() {
  const value = useContext(LocaleContext);
  if (!value) throw new Error("useLocale must be used inside LocaleProvider");
  return value;
}
