import { Plus, Tag, X } from "lucide-react";
import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { ProfileChip } from "@/features/chat/profile";
import type { Locale } from "@/features/chat/types";

const COPY = {
  fa: {
    title: "زمینه گفت‌وگو",
    empty: "همین‌طور که می‌پرسید، سرویس و پلتفرم شما اینجا ثبت می‌شود.",
    explain: "پاسخ‌ها با این زمینه تنظیم می‌شوند.",
    add: "افزودن",
    addLabel: "افزودن زمینه",
    placeholder: "مثلاً آلمان",
    remove: (value: string) => `حذف ${value}`,
    kinds: {
      platform: "پلتفرم",
      service: "سرویس",
      region: "منطقه",
      other: "زمینه",
    },
  },
  en: {
    title: "Conversation context",
    empty: "As you ask, your service and platform are recorded here.",
    explain: "Answers are tailored to this context.",
    add: "Add",
    addLabel: "Add context",
    placeholder: "e.g. Germany",
    remove: (value: string) => `Remove ${value}`,
    kinds: {
      platform: "Platform",
      service: "Service",
      region: "Region",
      other: "Context",
    },
  },
} as const;

interface ConversationContextProps {
  chips: readonly ProfileChip[];
  locale: Locale;
  onAdd: (value: string) => void;
  onRemove: (chip: ProfileChip) => void;
}

export function ConversationContext({
  chips,
  locale,
  onAdd,
  onRemove,
}: ConversationContextProps) {
  const copy = COPY[locale];
  const [draft, setDraft] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = draft.trim();
    if (!value) return;
    onAdd(value);
    setDraft("");
  };

  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-2 text-primary">
        <Tag className="size-4" />
        <h2 className="text-xs font-semibold tracking-wide">{copy.title}</h2>
      </div>

      {chips.length === 0 ? (
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          {copy.empty}
        </p>
      ) : (
        <>
          <ul className="mt-3 flex flex-wrap gap-2">
            {chips.map((chip) => (
              <li key={`${chip.kind}:${chip.value}`}>
                <span className="flex items-center gap-1.5 rounded-full border border-primary/25 bg-primary/8 py-1 ps-3 pe-1 text-sm">
                  <span className="text-[0.65rem] text-muted-foreground">
                    {copy.kinds[chip.kind]}
                  </span>
                  <span className="font-medium">{chip.value}</span>
                  <Button
                    aria-label={copy.remove(chip.value)}
                    className="size-5 rounded-full text-muted-foreground hover:text-foreground"
                    onClick={() => onRemove(chip)}
                    size="icon"
                    type="button"
                    variant="ghost"
                  >
                    <X className="size-3" />
                  </Button>
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs leading-6 text-muted-foreground">
            {copy.explain}
          </p>
        </>
      )}

      <form className="mt-4 flex gap-2" onSubmit={submit}>
        <label className="sr-only" htmlFor="context-add">
          {copy.addLabel}
        </label>
        <Input
          className="h-9"
          id="context-add"
          maxLength={40}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={copy.placeholder}
          value={draft}
        />
        <Button
          className="h-9 shrink-0"
          disabled={!draft.trim()}
          size="sm"
          type="submit"
          variant="outline"
        >
          <Plus className="size-4" />
          {copy.add}
        </Button>
      </form>
    </div>
  );
}
