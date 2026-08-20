import type { BundledLanguage } from "streamdown";
import { describe, expect, it } from "vitest";
import { limitedCodeHighlighter } from "./code-highlighter";

type HighlightResult = NonNullable<
  ReturnType<typeof limitedCodeHighlighter.highlight>
>;

const highlight = (language: string, code: string): Promise<HighlightResult> =>
  new Promise((resolve) => {
    const result = limitedCodeHighlighter.highlight(
      {
        code,
        language: language as BundledLanguage,
        themes: limitedCodeHighlighter.getThemes(),
      },
      resolve,
    );
    if (result) resolve(result);
  });

const textFrom = (result: HighlightResult): string =>
  result.tokens
    .map((line) => line.map((token) => token.content).join(""))
    .join("\n");

const hasSyntaxColors = (result: HighlightResult): boolean =>
  result.tokens
    .flat()
    .some((token) =>
      Boolean(
        (token.color && token.color !== "inherit") || token.htmlStyle?.color,
      ),
    );

describe("limited code highlighter", () => {
  it.each([
    "bash",
    "sh",
    "js",
    "javascript",
    "json",
    "python",
    "py",
    "php",
    "go",
    "ts",
    "typescript",
    "csharp",
    "cs",
    "html",
    "dockerfile",
  ])("supports the documented fence label %s", (language) => {
    expect(
      limitedCodeHighlighter.supportsLanguage(language as BundledLanguage),
    ).toBe(true);
  });

  it.each(["", "config", "conf", "laravel", "txt", "gitignore", "ruby"])(
    "keeps the unsupported fence label %s as plain text",
    async (language) => {
      const code = "GUNICORN_TIMEOUT=120\nliara.json";
      const result = await highlight(language, code);

      expect(textFrom(result)).toBe(code);
      expect(hasSyntaxColors(result)).toBe(false);
    },
  );

  it("treats an invalid JSON label as a hint and preserves the content", async () => {
    const code = "PORT=3000\nThis is configuration, not JSON.";
    const result = await highlight("json", code);

    expect(textFrom(result)).toBe(code);
    expect(hasSyntaxColors(result)).toBe(false);
  });

  it("highlights valid JSON", async () => {
    const code = '{"port": 3000, "enabled": true}';
    const result = await highlight("json", code);

    expect(textFrom(result)).toBe(code);
    expect(hasSyntaxColors(result)).toBe(true);
  });
});
