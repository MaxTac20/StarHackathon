import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { BookOpen, MessageSquareText, RotateCcw, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
} from "@/components/ai-elements/prompt-input";
import { Suggestion, Suggestions } from "@/components/ai-elements/suggestion";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ConversationContext } from "@/features/chat/components/conversation-context";
import {
  deriveChips,
  loadChips,
  mergeChips,
  type ProfileChip,
  saveChips,
} from "@/features/chat/profile";
import { chatCopy } from "@/features/chat/copy";
import { ChatMessage } from "@/features/chat/components/chat-message";
import type {
  ChatSource,
  LiaraChatMessage,
  Locale,
} from "@/features/chat/types";
import { cn } from "@/lib/utils";

export function ChatExperience() {
  const [locale, setLocale] = useState<Locale>("fa");
  const [input, setInput] = useState("");
  const [chips, setChips] = useState<ProfileChip[]>(loadChips);
  const copy = chatCopy[locale];

  // The transport closes over the chips, so it has to be rebuilt when they
  // change or a send would carry the previous context.
  const transport = useMemo(
    () =>
      new DefaultChatTransport<LiaraChatMessage>({
        api: "/api/chat",
        body: { profile: chips },
      }),
    [chips],
  );
  const {
    clearError,
    error,
    messages,
    sendMessage,
    setMessages,
    status,
    stop,
  } = useChat<LiaraChatMessage>({
    transport,
  });
  const isGenerating = status === "submitted" || status === "streaming";

  useEffect(() => {
    document.documentElement.dir = locale === "fa" ? "rtl" : "ltr";
    document.documentElement.lang = locale;
  }, [locale]);

  // Context is derived from the pages that actually grounded an answer, so a
  // chip always has a reason a user can trace. Persisted per browser: the
  // session is the scope, there are no accounts.
  const streamedSources = useMemo(
    () =>
      messages.flatMap((message) =>
        message.parts.flatMap((part) =>
          part.type === "data-sources" ? (part.data as ChatSource[]) : [],
        ),
      ),
    [messages],
  );

  useEffect(() => {
    if (streamedSources.length === 0) return;
    setChips((current) => {
      const merged = mergeChips(current, deriveChips(streamedSources));
      return merged.length === current.length ? current : merged;
    });
  }, [streamedSources]);

  useEffect(() => {
    saveChips(chips);
  }, [chips]);

  const addChip = (value: string) =>
    setChips((current) => mergeChips(current, [{ kind: "other", value }]));

  const removeChip = (chip: ProfileChip) =>
    setChips((current) =>
      current.filter(
        (item) => !(item.kind === chip.kind && item.value === chip.value),
      ),
    );

  const submitText = async (text: string) => {
    const value = text.trim();
    if (!value || isGenerating) return;
    clearError();
    await sendMessage({ text: value });
    setInput("");
  };

  const handleSubmit = async (message: PromptInputMessage) => {
    await submitText(message.text);
  };

  const startNewChat = () => {
    stop();
    clearError();
    setMessages([]);
    setInput("");
  };

  return (
    <div
      className="min-h-dvh bg-background text-foreground"
      dir={locale === "fa" ? "rtl" : "ltr"}
      lang={locale}
    >
      <div className="mx-auto flex min-h-dvh w-full max-w-[1480px] flex-col p-3 sm:p-5 lg:h-dvh lg:overflow-hidden lg:p-7">
        <header className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/80 bg-background/85 px-4 py-3 shadow-sm backdrop-blur-xl sm:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-[0_8px_24px_color-mix(in_oklab,var(--primary)_24%,transparent)]">
              <BookOpen />
            </div>
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold tracking-wide text-primary">
                {copy.brandEyebrow}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <fieldset className="m-0 flex rounded-xl border bg-muted/50 p-1">
              <legend className="sr-only">Language</legend>
              {(["fa", "en"] as const).map((language) => (
                <Button
                  aria-pressed={locale === language}
                  className="h-8 min-w-10 rounded-lg px-2.5"
                  key={language}
                  onClick={() => setLocale(language)}
                  size="sm"
                  type="button"
                  variant={locale === language ? "default" : "ghost"}
                >
                  {language === "fa" ? "فا" : "EN"}
                </Button>
              ))}
            </fieldset>
            <Button
              aria-label={copy.newChat}
              onClick={startNewChat}
              size="icon"
              title={copy.newChat}
              type="button"
              variant="outline"
            >
              <RotateCcw />
            </Button>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 gap-3 lg:grid-cols-[290px_minmax(0,1fr)]">
          <aside className="order-2 flex flex-col rounded-2xl border border-border/80 bg-background/78 p-4 shadow-sm backdrop-blur-xl lg:order-1">
            <ConversationContext
              chips={chips}
              locale={locale}
              onAdd={addChip}
              onRemove={removeChip}
            />
          </aside>

          <section className="order-1 flex h-[calc(100dvh-10rem)] min-h-[32rem] min-w-0 flex-col overflow-hidden rounded-2xl border border-border/80 bg-card/88 shadow-[0_24px_80px_color-mix(in_oklab,var(--foreground)_8%,transparent)] backdrop-blur-xl lg:order-2 lg:h-auto lg:min-h-0">
            <div className="flex items-center justify-between border-b border-border/70 px-4 py-3 sm:px-6">
              <div className="flex items-center gap-2">
                <MessageSquareText className="text-primary" />
                <span className="text-sm font-semibold">
                  {locale === "fa" ? "گفت‌وگو" : "Conversation"}
                </span>
              </div>
              <span
                className={cn(
                  "flex items-center gap-2 text-xs text-muted-foreground",
                  isGenerating && "text-primary",
                )}
              >
                <span
                  className={cn(
                    "size-2 rounded-full bg-muted-foreground/45",
                    isGenerating && "animate-pulse bg-primary",
                  )}
                />
                {isGenerating
                  ? locale === "fa"
                    ? "پاسخ در حال رسیدن است"
                    : "Answer is streaming"
                  : locale === "fa"
                    ? "آماده"
                    : "Ready"}
              </span>
            </div>

            <Conversation className="min-h-0 min-w-0">
              <ConversationContent className="mx-auto min-w-0 w-full max-w-4xl gap-7 px-4 py-7 sm:px-7">
                {messages.length === 0 ? (
                  <ConversationEmptyState className="min-h-[46dvh] min-w-0 max-w-full p-0 text-start">
                    <div className="mx-auto flex w-full min-w-0 max-w-2xl flex-col items-center text-center">
                      <div className="mb-5 flex size-14 items-center justify-center rounded-2xl border bg-muted/55 text-primary shadow-sm">
                        <Sparkles />
                      </div>
                      <p className="text-xs font-semibold tracking-wide text-primary">
                        {copy.emptyEyebrow}
                      </p>
                      <h2 className="mt-3 text-balance text-2xl font-bold leading-[1.45] tracking-tight sm:text-4xl">
                        {copy.emptyTitle}
                      </h2>
                      <p className="mt-3 max-w-xl text-sm leading-7 text-muted-foreground sm:text-base">
                        {copy.emptyDescription}
                      </p>
                      <div className="mt-7 min-w-0 w-full">
                        <p className="mb-3 text-xs font-medium text-muted-foreground">
                          {copy.suggestionsLabel}
                        </p>
                        <Suggestions
                          className="justify-start pb-2 sm:justify-center"
                          dir={locale === "fa" ? "rtl" : "ltr"}
                        >
                          {copy.suggestions.map((suggestion) => (
                            <Suggestion
                              className="h-auto max-w-[calc(100cqw-0.5rem)] whitespace-normal rounded-xl px-4 py-2.5 text-start leading-6 sm:max-w-[18rem]"
                              disabled={isGenerating}
                              key={suggestion}
                              onClick={submitText}
                              suggestion={suggestion}
                            />
                          ))}
                        </Suggestions>
                      </div>
                    </div>
                  </ConversationEmptyState>
                ) : (
                  messages.map((message, index) => (
                    <ChatMessage
                      isLast={index === messages.length - 1}
                      isStreaming={status === "streaming"}
                      key={message.id}
                      locale={locale}
                      message={message}
                    />
                  ))
                )}

                {error ? (
                  <Alert className="rounded-2xl" variant="destructive">
                    <AlertTitle>{copy.errorTitle}</AlertTitle>
                    <AlertDescription className="mt-1 leading-7">
                      {copy.errorText}
                      <Button
                        className="mt-2"
                        onClick={clearError}
                        size="sm"
                        type="button"
                        variant="outline"
                      >
                        {copy.dismiss}
                      </Button>
                    </AlertDescription>
                  </Alert>
                ) : null}
              </ConversationContent>
              <ConversationScrollButton
                aria-label={
                  locale === "fa" ? "رفتن به آخر گفتگو" : "Jump to latest"
                }
              />
            </Conversation>

            <div className="border-t border-border/70 bg-background/88 p-3 backdrop-blur-xl sm:p-4">
              <div className="mx-auto max-w-4xl">
                <PromptInput className="rounded-2xl" onSubmit={handleSubmit}>
                  <PromptInputBody>
                    <PromptInputTextarea
                      aria-label={copy.inputPlaceholder}
                      className="min-h-20 px-1 text-[0.95rem] leading-7"
                      dir="auto"
                      onChange={(event) => setInput(event.currentTarget.value)}
                      placeholder={copy.inputPlaceholder}
                      value={input}
                    />
                  </PromptInputBody>
                  <PromptInputFooter>
                    <PromptInputTools>
                      <span className="text-[0.68rem] text-muted-foreground sm:text-xs">
                        {copy.inputHint}
                      </span>
                    </PromptInputTools>
                    <PromptInputSubmit
                      aria-label={isGenerating ? copy.stop : copy.send}
                      disabled={!isGenerating && !input.trim()}
                      onStop={stop}
                      status={status}
                      title={isGenerating ? copy.stop : copy.send}
                    />
                  </PromptInputFooter>
                </PromptInput>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
