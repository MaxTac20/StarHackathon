import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import { BidiText } from "@/features/chat/components/bidi-text";

test("keeps embedded Latin identifiers isolated inside Persian prose", () => {
  const text = "برای liara.json مقدار GUNICORN_TIMEOUT را تنظیم کنید.";
  const { container } = render(<BidiText>{text}</BidiText>);

  const rendered = container.querySelector("span");
  expect(rendered).not.toBeNull();
  if (!rendered) throw new Error("BidiText did not render its span");
  expect(rendered).toHaveAttribute("dir", "rtl");
  expect(rendered).toHaveTextContent(text);
  expect(
    Array.from(rendered.querySelectorAll("bdi")).map((node) => ({
      direction: node.getAttribute("dir"),
      text: node.textContent,
    })),
  ).toEqual([
    { direction: "ltr", text: "liara.json" },
    { direction: "ltr", text: "GUNICORN_TIMEOUT" },
  ]);
});
