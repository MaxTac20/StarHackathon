import type { ChatSource } from "@/features/chat/types";

export type ProfileKind = "platform" | "service" | "region" | "other";

export type ProfileChip = {
  kind: ProfileKind;
  value: string;
};

const STORAGE_KEY = "liara.conversation-context";
const MAX_CHIPS = 8;

/**
 * Documentation paths encode the stack: `paas/django/how-tos/deploy-app` is the
 * Django platform on PaaS. Deriving context from the pages that actually
 * grounded an answer is honest and costs nothing, where asking a model to infer
 * it would cost a call and could be wrong.
 */
const SERVICES: Record<string, string> = {
  paas: "PaaS",
  dbaas: "Database",
  "object-storage": "Object Storage",
  "email-server": "Email Server",
  iaas: "Cloud Server",
  "dns-management-system": "DNS",
  "one-click-apps": "One-Click Apps",
  ai: "AI",
};

const PLATFORMS: Record<string, string> = {
  nodejs: "Node.js",
  nextjs: "Next.js",
  laravel: "Laravel",
  python: "Python",
  django: "Django",
  go: "Go",
  php: "PHP",
  docker: "Docker",
  flask: "Flask",
  dotnet: ".NET",
  react: "React",
  static: "Static",
  vue: "Vue",
  angular: "Angular",
};

const key = (chip: ProfileChip) => `${chip.kind}:${chip.value.toLowerCase()}`;

/**
 * Only the single most-cited platform and service are promoted, and only when a
 * page actually named them. A wrong chip is worse than a missing one: the user
 * has to notice and remove it, and it shades every later answer until they do.
 */
export function deriveChips(sources: readonly ChatSource[]): ProfileChip[] {
  const platforms = new Map<string, number>();
  const services = new Map<string, number>();

  for (const source of sources) {
    const [first, second] = source.path.split("/");
    const service = SERVICES[first ?? ""];
    if (service) services.set(service, (services.get(service) ?? 0) + 1);
    const platform = PLATFORMS[second ?? ""];
    if (platform) platforms.set(platform, (platforms.get(platform) ?? 0) + 1);
  }

  const top = (counts: Map<string, number>) =>
    [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];

  const chips: ProfileChip[] = [];
  const platform = top(platforms);
  const service = top(services);
  if (platform) chips.push({ kind: "platform", value: platform });
  if (service) chips.push({ kind: "service", value: service });
  return chips;
}

export function mergeChips(
  existing: readonly ProfileChip[],
  incoming: readonly ProfileChip[],
): ProfileChip[] {
  const seen = new Set(existing.map(key));
  const merged = [...existing];
  for (const chip of incoming) {
    if (seen.has(key(chip))) continue;
    seen.add(key(chip));
    merged.push(chip);
  }
  return merged.slice(0, MAX_CHIPS);
}

export function loadChips(): ProfileChip[] {
  try {
    const raw = globalThis.localStorage?.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(
        (chip): chip is ProfileChip =>
          typeof chip === "object" &&
          chip !== null &&
          typeof (chip as ProfileChip).value === "string" &&
          (chip as ProfileChip).value.length > 0 &&
          ["platform", "service", "region", "other"].includes(
            (chip as ProfileChip).kind,
          ),
      )
      .slice(0, MAX_CHIPS);
  } catch {
    // A corrupt or unavailable store must not take the conversation down with it.
    return [];
  }
}

export function saveChips(chips: readonly ProfileChip[]): void {
  try {
    globalThis.localStorage?.setItem(STORAGE_KEY, JSON.stringify(chips));
  } catch {
    // Private browsing and quota limits are not worth failing a send over.
  }
}
