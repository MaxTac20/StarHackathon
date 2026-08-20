import {
  BookOpenText,
  ChevronDown,
  FileWarning,
  ShieldCheck,
} from "lucide-react";
import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from "@/components/ai-elements/reasoning";
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from "@/components/ai-elements/sources";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { chatCopy } from "@/features/chat/copy";
import { BidiText } from "@/features/chat/components/bidi-text";
import { PipelineStatus } from "@/features/chat/components/pipeline-status";
import type {
  ChatNotice,
  ChatSource,
  ChatStatusData,
  LiaraChatMessage,
  Locale,
} from "@/features/chat/types";

const STREAMING_MARKDOWN_REMEND = { linkMode: "text-only" } as const;

function collectMessageParts(message: LiaraChatMessage) {
  let status: ChatStatusData | undefined;
  let sources: ChatSource[] = [];
  const notices: ChatNotice[] = [];
  const reasoning: string[] = [];
  const text: string[] = [];

  for (const part of message.parts) {
    switch (part.type) {
      case "data-status":
        status = part.data as ChatStatusData;
        break;
      case "data-sources":
        sources = part.data as ChatSource[];
        break;
      case "data-notice":
        notices.push(part.data as ChatNotice);
        break;
      case "reasoning":
        reasoning.push(part.text);
        break;
      case "text":
        text.push(part.text);
        break;
      default:
        break;
    }
  }

  return {
    notices,
    reasoning: reasoning.join(""),
    sources,
    status,
    text: text.join(""),
  };
}

export function ChatMessage({
  isLast,
  isStreaming,
  locale,
  message,
}: {
  isLast: boolean;
  isStreaming: boolean;
  locale: Locale;
  message: LiaraChatMessage;
}) {
  const copy = chatCopy[locale];
  const parts = collectMessageParts(message);

  if (message.role === "user") {
    return (
      <Message from="user">
        <MessageContent className="max-w-[88%] rounded-2xl rounded-ee-md px-4 py-3 text-[0.95rem] leading-7 sm:max-w-[75%]">
          <BidiText>{parts.text}</BidiText>
        </MessageContent>
      </Message>
    );
  }

  return (
    <Message className="max-w-full" from="assistant">
      <MessageContent className="w-full gap-4 overflow-visible">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
          <span className="flex size-7 items-center justify-center rounded-full border bg-background text-primary shadow-sm">
            <ShieldCheck />
          </span>
          <span>{locale === "fa" ? "راهنمای لیارا" : "Liara guide"}</span>
        </div>

        {parts.status ? (
          <PipelineStatus locale={locale} status={parts.status} />
        ) : null}

        {parts.sources.length > 0 ? (
          <Sources className="mb-0 rounded-2xl border border-border/80 bg-background p-3">
            <SourcesTrigger
              className="w-full justify-between"
              count={parts.sources.length}
            >
              <span className="flex items-center gap-2 font-medium">
                <BookOpenText />
                {copy.sources(parts.sources.length)}
              </span>
              <ChevronDown />
            </SourcesTrigger>
            <SourcesContent className="w-full">
              {parts.sources.map((source, index) => (
                <Source
                  className="group rounded-xl border border-transparent px-2 py-2 text-foreground transition-colors hover:border-border hover:bg-muted/60"
                  href={source.cite_url}
                  key={source.cite_url}
                  title={source.title}
                >
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 font-mono text-[0.68rem] text-primary">
                    {index + 1}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium">
                      {source.title}
                    </span>
                    <bdi
                      className="block truncate font-mono text-[0.68rem] text-muted-foreground"
                      dir="ltr"
                    >
                      {source.path}
                    </bdi>
                  </span>
                </Source>
              ))}
            </SourcesContent>
          </Sources>
        ) : null}

        {parts.reasoning ? (
          <Reasoning
            className="mb-0 rounded-2xl border border-border/70 bg-muted/25 p-3"
            isStreaming={isLast && isStreaming && !parts.text}
          >
            <ReasoningTrigger
              getThinkingMessage={(streaming, duration) =>
                streaming
                  ? copy.reasoningStreaming
                  : copy.reasoningDone(duration)
              }
            />
            <ReasoningContent className="bidi-plaintext leading-7" dir="auto">
              {parts.reasoning}
            </ReasoningContent>
          </Reasoning>
        ) : null}

        {parts.text ? (
          <MessageResponse
            className="chat-prose text-[0.98rem] leading-8"
            dir="auto"
            isAnimating={isLast && isStreaming}
            remend={STREAMING_MARKDOWN_REMEND}
          >
            {parts.text}
          </MessageResponse>
        ) : null}

        {parts.notices.map((notice) => (
          <Alert
            className="rounded-2xl bg-muted/35"
            key={`${notice.kind}-${notice.text}`}
          >
            <FileWarning />
            <AlertTitle>{copy.noticeTitle}</AlertTitle>
            <AlertDescription className="bidi-plaintext leading-7" dir="auto">
              {notice.text}
            </AlertDescription>
          </Alert>
        ))}
      </MessageContent>
    </Message>
  );
}
