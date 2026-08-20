import type { UIMessage } from "ai";

export const CHAT_PHASES = [
  "understanding",
  "retrieving",
  "reading",
  "drafting",
] as const;

export type ChatPhase = (typeof CHAT_PHASES)[number];

export interface ChatStatusData {
  phase: string;
  label: string;
}

export interface ChatSource {
  title: string;
  cite_url: string;
  path: string;
}

export interface ChatNotice {
  kind: "defect" | "gap";
  text: string;
}

export interface ChatDataParts extends Record<string, unknown> {
  status: ChatStatusData;
  sources: ChatSource[];
  notice: ChatNotice;
}

export type LiaraChatMessage = UIMessage<never, ChatDataParts>;
export type Locale = "fa" | "en";
