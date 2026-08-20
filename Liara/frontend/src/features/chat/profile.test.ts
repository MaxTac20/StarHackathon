import { describe, expect, it } from "vitest";

import { deriveChips, mergeChips } from "@/features/chat/profile";
import type { ChatSource } from "@/features/chat/types";

const source = (path: string): ChatSource => ({
  title: path,
  cite_url: `https://docs.liara.ir/${path}/`,
  path,
});

describe("deriveChips", () => {
  it("reads the stack from the paths that grounded the answer", () => {
    expect(
      deriveChips([
        source("paas/django/how-tos/deploy-app"),
        source("paas/django/fix-common-errors/worker-timeout"),
      ]),
    ).toEqual([
      { kind: "platform", value: "Django" },
      { kind: "service", value: "PaaS" },
    ]);
  });

  it("promotes only the dominant platform when sources disagree", () => {
    const chips = deriveChips([
      source("paas/django/how-tos/deploy-app"),
      source("paas/django/quick-start"),
      source("paas/flask/quick-start"),
    ]);
    expect(chips).toContainEqual({ kind: "platform", value: "Django" });
    expect(chips).not.toContainEqual({ kind: "platform", value: "Flask" });
  });

  it("claims nothing when no path names a platform", () => {
    expect(deriveChips([source("references/cli/create-liara-json")])).toEqual(
      [],
    );
  });
});

describe("mergeChips", () => {
  it("does not resurrect a chip the user removed in this pass", () => {
    // Removal is the user overruling the derivation; re-adding it in the same
    // merge would make the remove button appear broken.
    const merged = mergeChips(
      [{ kind: "service", value: "PaaS" }],
      [
        { kind: "service", value: "PaaS" },
        { kind: "platform", value: "Go" },
      ],
    );
    expect(merged).toEqual([
      { kind: "service", value: "PaaS" },
      { kind: "platform", value: "Go" },
    ]);
  });

  it("is case-insensitive so a typed chip does not duplicate a derived one", () => {
    expect(
      mergeChips(
        [{ kind: "platform", value: "Django" }],
        [{ kind: "platform", value: "django" }],
      ),
    ).toHaveLength(1);
  });

  it("caps the list so the panel cannot grow without bound", () => {
    const many = Array.from({ length: 12 }, (_, index) => ({
      kind: "other" as const,
      value: `chip-${index}`,
    }));
    expect(mergeChips([], many)).toHaveLength(8);
  });
});
