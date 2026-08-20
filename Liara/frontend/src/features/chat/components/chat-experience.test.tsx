import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test } from "vitest";
import { ChatExperience } from "@/features/chat/components/chat-experience";

const suggestionScroller = (): HTMLElement => {
  const viewport = document.querySelector<HTMLElement>(
    "[data-radix-scroll-area-viewport]",
  );
  if (!viewport) throw new Error("Suggestion scroller did not render");
  return viewport;
};

test("opens suggestions at the reading-order origin for each language", async () => {
  const user = userEvent.setup();
  render(<ChatExperience />);

  expect(getComputedStyle(suggestionScroller()).direction).toBe("rtl");

  await user.click(screen.getByRole("button", { name: "EN" }));

  expect(getComputedStyle(suggestionScroller()).direction).toBe("ltr");
});
