import { Check, CircleDotDashed } from "lucide-react";
import { Shimmer } from "@/components/ai-elements/shimmer";
import { chatCopy } from "@/features/chat/copy";
import {
  CHAT_PHASES,
  type ChatPhase,
  type ChatStatusData,
  type Locale,
} from "@/features/chat/types";
import { cn } from "@/lib/utils";

function isKnownPhase(phase: string): phase is ChatPhase {
  return CHAT_PHASES.some((candidate) => candidate === phase);
}

export function PipelineStatus({
  locale,
  status,
}: {
  locale: Locale;
  status: ChatStatusData;
}) {
  const copy = chatCopy[locale];
  const currentIndex = isKnownPhase(status.phase)
    ? CHAT_PHASES.indexOf(status.phase)
    : -1;

  return (
    <section
      aria-label={copy.genericProgress}
      aria-live="polite"
      className="rounded-2xl border border-border/80 bg-muted/45 p-3 sm:p-4"
      data-testid="pipeline-status"
    >
      <ol className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {CHAT_PHASES.map((phase, index) => {
          const complete = currentIndex > index;
          const active = currentIndex === index;
          return (
            <li
              className={cn(
                "flex min-w-0 items-center gap-2 rounded-xl px-2.5 py-2 text-xs",
                active && "bg-background text-foreground shadow-sm",
                !active && "text-muted-foreground",
              )}
              key={phase}
            >
              <span
                className={cn(
                  "flex size-5 shrink-0 items-center justify-center rounded-full border",
                  (active || complete) && "border-primary text-primary",
                )}
              >
                {complete ? <Check /> : <CircleDotDashed />}
              </span>
              <span className="truncate">
                {active ? (
                  <Shimmer duration={1.4}>{copy.phaseLabels[phase]}</Shimmer>
                ) : (
                  copy.phaseLabels[phase]
                )}
              </span>
            </li>
          );
        })}
      </ol>
      {currentIndex === -1 ? (
        <p className="mt-2 text-xs text-muted-foreground">
          {status.label || copy.genericProgress}
        </p>
      ) : null}
    </section>
  );
}
