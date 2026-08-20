import { Fragment, type ReactNode } from "react";
import { cn } from "@/lib/utils";

const LATIN_TOKEN_RE =
  /(https?:\/\/[^\s]+|(?:[A-Za-z0-9_./:@+-]*[A-Za-z][A-Za-z0-9_./:@+-]*))/g;
const PERSIAN_LETTER_RE = /[\u0600-\u06ff]/;
const LATIN_LETTER_RE = /[A-Za-z]/;

export function textDirection(text: string): "rtl" | "ltr" {
  for (const character of text) {
    if (PERSIAN_LETTER_RE.test(character)) return "rtl";
    if (LATIN_LETTER_RE.test(character)) return "ltr";
  }
  return "ltr";
}

export function BidiText({
  children,
  className,
}: {
  children: string;
  className?: string;
}) {
  const parts: ReactNode[] = [];
  let cursor = 0;

  for (const match of children.matchAll(LATIN_TOKEN_RE)) {
    const index = match.index;
    const token = match[0];
    if (index > cursor) {
      parts.push(children.slice(cursor, index));
    }
    parts.push(
      <bdi dir="ltr" key={`${index}-${token}`}>
        {token}
      </bdi>,
    );
    cursor = index + token.length;
  }

  if (cursor < children.length) {
    parts.push(children.slice(cursor));
  }

  return (
    <span
      className={cn("bidi-plaintext", className)}
      dir={textDirection(children)}
    >
      {parts.map((part, index) => (
        <Fragment key={typeof part === "string" ? `${index}-${part}` : index}>
          {part}
        </Fragment>
      ))}
    </span>
  );
}
