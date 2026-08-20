import type { ChatPhase, Locale } from "@/features/chat/types";

interface ChatCopy {
  brandEyebrow: string;
  brandTitle: string;
  brandSubtitle: string;
  demoBadge: string;
  newChat: string;
  emptyEyebrow: string;
  emptyTitle: string;
  emptyDescription: string;
  suggestionsLabel: string;
  suggestions: string[];
  inputPlaceholder: string;
  inputHint: string;
  send: string;
  stop: string;
  sources: (count: number) => string;
  noticeTitle: string;
  errorTitle: string;
  errorText: string;
  dismiss: string;
  reasoningStreaming: string;
  reasoningDone: (duration?: number) => string;
  phaseLabels: Record<ChatPhase, string>;
  genericProgress: string;
  evidenceTitle: string;
  evidenceItems: string[];
}

export const chatCopy: Record<Locale, ChatCopy> = {
  fa: {
    brandEyebrow: "راهنمای مستندات لیارا",
    brandTitle: "پرسش را بپرس؛ مسیر پاسخ را ببین.",
    brandSubtitle:
      "پاسخ‌های دوزبانه با منبع دقیق، کد خوانا و وضعیت واقعی هر مرحله.",
    demoBadge: "جریان نمایشی",
    newChat: "گفت‌وگوی تازه",
    emptyEyebrow: "از مستندات رسمی لیارا",
    emptyTitle: "برای deploy بعدی چه چیزی مبهم است؟",
    emptyDescription:
      "درباره PaaS، دیسک، متغیر محیطی یا خطاهای رایج بپرسید. پاسخ همراه با منبع و قدم بعدی می‌آید.",
    suggestionsLabel: "چند پرسش برای شروع",
    suggestions: [
      "چطور GUNICORN_TIMEOUT را در لیارا تنظیم کنم؟",
      "برای نگه‌داری فایل‌ها بعد از deploy چه کار کنم؟",
      "How do I set an environment variable with Liara CLI?",
    ],
    inputPlaceholder: "مثلاً: چرا فایل‌های آپلودشده بعد از deploy پاک می‌شوند؟",
    inputHint: "Enter برای ارسال · Shift + Enter برای خط جدید",
    send: "ارسال پرسش",
    stop: "توقف پاسخ",
    sources: (count) => `${count.toLocaleString("fa-IR")} منبع بررسی‌شده`,
    noticeTitle: "نکته درباره مستندات",
    errorTitle: "پاسخ کامل نشد",
    errorText:
      "جریان پاسخ به‌صورت امن بسته شد. دوباره تلاش کنید؛ جزئیات داخلی سرویس نمایش داده نمی‌شود.",
    dismiss: "بستن",
    reasoningStreaming: "در حال جمع‌بندی شواهد",
    reasoningDone: (duration) =>
      duration ? `جمع‌بندی شواهد در ${duration} ثانیه` : "شواهد جمع‌بندی شد",
    phaseLabels: {
      understanding: "درک پرسش",
      retrieving: "جست‌وجو",
      reading: "بررسی منابع",
      drafting: "تدوین پاسخ",
    },
    genericProgress: "در حال ادامه پردازش",
    evidenceTitle: "این رابط چه چیزی را نشان می‌دهد؟",
    evidenceItems: [
      "حرکت اولیه از مرحله واقعی stream می‌آید.",
      "منابع پیش از تولید پاسخ ظاهر می‌شوند.",
      "کد و شناسه‌های لاتین در متن فارسی ایزوله‌اند.",
    ],
  },
  en: {
    brandEyebrow: "Liara documentation guide",
    brandTitle: "Ask the question. Watch the answer take shape.",
    brandSubtitle:
      "Bilingual answers with precise sources, readable code, and honest pipeline stages.",
    demoBadge: "Fixture stream",
    newChat: "New conversation",
    emptyEyebrow: "Grounded in Liara documentation",
    emptyTitle: "What is unclear about your next deploy?",
    emptyDescription:
      "Ask about PaaS, disks, environment variables, or common failures. The answer arrives with sources and a practical next step.",
    suggestionsLabel: "Try one of these",
    suggestions: [
      "How do I set an environment variable with Liara CLI?",
      "Why do uploaded files disappear after a deploy?",
      "چطور GUNICORN_TIMEOUT را در لیارا تنظیم کنم؟",
    ],
    inputPlaceholder:
      "For example: why do uploaded files disappear after a deploy?",
    inputHint: "Enter to send · Shift + Enter for a new line",
    send: "Send question",
    stop: "Stop response",
    sources: (count) => `${count} reviewed source${count === 1 ? "" : "s"}`,
    noticeTitle: "Documentation note",
    errorTitle: "The answer did not finish",
    errorText:
      "The stream closed safely. Try again; internal service details are never shown here.",
    dismiss: "Dismiss",
    reasoningStreaming: "Synthesizing the evidence",
    reasoningDone: (duration) =>
      duration
        ? `Synthesized evidence in ${duration}s`
        : "Evidence synthesized",
    phaseLabels: {
      understanding: "Understand",
      retrieving: "Retrieve",
      reading: "Read sources",
      drafting: "Draft answer",
    },
    genericProgress: "Continuing the pipeline",
    evidenceTitle: "What this surface makes visible",
    evidenceItems: [
      "The first motion comes from a real stream stage.",
      "Sources land before answer generation starts.",
      "Latin identifiers stay isolated inside Persian prose.",
    ],
  },
};
