import { createHighlighterCore, type HighlighterCore } from "@shikijs/core";
import { createJavaScriptRegexEngine } from "@shikijs/engine-javascript";
import githubDark from "@shikijs/themes/github-dark";
import githubLight from "@shikijs/themes/github-light";
import type {
  CodeHighlighterPlugin,
  HighlightOptions,
  HighlightResult,
} from "streamdown";

const themes = ["github-light", "github-dark"] as const;

const languageLoaders = {
  csharp: () =>
    import("@shikijs/langs/csharp").then((module) => module.default),
  docker: () =>
    import("@shikijs/langs/dockerfile").then((module) => module.default),
  go: () => import("@shikijs/langs/go").then((module) => module.default),
  html: () => import("@shikijs/langs/html").then((module) => module.default),
  javascript: () =>
    import("@shikijs/langs/javascript").then((module) => module.default),
  json: () => import("@shikijs/langs/json").then((module) => module.default),
  php: () => import("@shikijs/langs/php").then((module) => module.default),
  python: () =>
    import("@shikijs/langs/python").then((module) => module.default),
  shellscript: () =>
    import("@shikijs/langs/bash").then((module) => module.default),
  typescript: () =>
    import("@shikijs/langs/typescript").then((module) => module.default),
} as const;

type HighlightLanguage = keyof typeof languageLoaders;

const languageAliases: Readonly<Record<string, HighlightLanguage>> = {
  bash: "shellscript",
  "c#": "csharp",
  cs: "csharp",
  csharp: "csharp",
  dockerfile: "docker",
  go: "go",
  html: "html",
  javascript: "javascript",
  js: "javascript",
  json: "json",
  php: "php",
  py: "python",
  python: "python",
  sh: "shellscript",
  shellscript: "shellscript",
  ts: "typescript",
  typescript: "typescript",
};

const highlighterPromise = createHighlighterCore({
  engine: createJavaScriptRegexEngine({ forgiving: true }),
  langs: [],
  themes: [githubLight, githubDark],
});

const languagePromises = new Map<HighlightLanguage, Promise<HighlighterCore>>();
const highlightedResults = new Map<string, HighlightResult>();
const pendingCallbacks = new Map<
  string,
  Set<(result: HighlightResult) => void>
>();

const normalizeLanguage = (language: string): HighlightLanguage | null =>
  languageAliases[language.trim().toLowerCase()] ?? null;

const isValidJson = (code: string): boolean => {
  try {
    JSON.parse(code);
    return true;
  } catch {
    return false;
  }
};

const plainTextResult = (code: string): HighlightResult => ({
  tokens: code.split("\n").map((line) => [
    {
      color: "inherit",
      content: line,
      htmlStyle: {},
      offset: 0,
    },
  ]),
});

const loadLanguage = (
  language: HighlightLanguage,
): Promise<HighlighterCore> => {
  const pending = languagePromises.get(language);
  if (pending) return pending;

  const languagePromise = Promise.all([
    highlighterPromise,
    languageLoaders[language](),
  ]).then(async ([highlighter, registrations]) => {
    await highlighter.loadLanguage(...registrations);
    return highlighter;
  });

  languagePromises.set(language, languagePromise);
  return languagePromise;
};

const resultKey = (code: string, language: HighlightLanguage): string =>
  `${language}:${code}`;

const highlight = (
  { code, language }: HighlightOptions,
  callback?: (result: HighlightResult) => void,
): HighlightResult | null => {
  const normalizedLanguage = normalizeLanguage(language);
  if (
    !normalizedLanguage ||
    (normalizedLanguage === "json" && !isValidJson(code))
  ) {
    return plainTextResult(code);
  }

  const key = resultKey(code, normalizedLanguage);
  const cached = highlightedResults.get(key);
  if (cached) return cached;

  if (callback) {
    const callbacks = pendingCallbacks.get(key) ?? new Set();
    callbacks.add(callback);
    pendingCallbacks.set(key, callbacks);
  }

  void loadLanguage(normalizedLanguage)
    .then((highlighter) => {
      const result = highlighter.codeToTokens(code, {
        lang: normalizedLanguage,
        themes: { dark: themes[1], light: themes[0] },
      });
      highlightedResults.set(key, result);
      for (const pendingCallback of pendingCallbacks.get(key) ?? []) {
        pendingCallback(result);
      }
      pendingCallbacks.delete(key);
    })
    .catch(() => {
      const result = plainTextResult(code);
      for (const pendingCallback of pendingCallbacks.get(key) ?? []) {
        pendingCallback(result);
      }
      pendingCallbacks.delete(key);
    });

  return null;
};

export const limitedCodeHighlighter = {
  getSupportedLanguages: () => Object.keys(languageAliases),
  getThemes: () => [...themes],
  highlight,
  name: "shiki",
  supportsLanguage: (language) => normalizeLanguage(language) !== null,
  type: "code-highlighter",
} satisfies CodeHighlighterPlugin;
