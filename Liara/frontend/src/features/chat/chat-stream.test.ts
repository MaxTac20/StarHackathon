import { DefaultChatTransport, type UIMessage, type UIMessageChunk } from "ai";
import { expect, test, vi } from "vitest";

async function collect(
  transport: DefaultChatTransport<UIMessage>,
): Promise<UIMessageChunk[]> {
  const stream = await transport.sendMessages({
    abortSignal: undefined,
    chatId: "stream-test",
    messageId: undefined,
    messages: [],
    trigger: "submit-message",
  });
  const reader = stream.getReader();
  const chunks: UIMessageChunk[] = [];

  while (true) {
    const { done, value } = await reader.read();
    if (done) return chunks;
    chunks.push(value);
  }
}

function transportFor(body: string) {
  return new DefaultChatTransport({
    fetch: vi.fn().mockResolvedValue(
      new Response(body, {
        headers: { "Content-Type": "text/event-stream" },
        status: 200,
      }),
    ),
  });
}

test("rejects a malformed JSON event instead of inventing a message", async () => {
  const transport = transportFor("data: {bad-json}\n\ndata: [DONE]\n\n");

  await expect(collect(transport)).rejects.toThrow("JSON parsing failed");
});

test("closes a truncated stream while preserving only complete events", async () => {
  const transport = transportFor(
    [
      'data: {"type":"text-start","id":"answer"}\n\n',
      'data: {"type":"text-delta","id":"answer","delta":"partial"}\n\n',
      'data: {"type":"text-delta"',
    ].join(""),
  );

  await expect(collect(transport)).resolves.toEqual([
    { type: "text-start", id: "answer" },
    { type: "text-delta", id: "answer", delta: "partial" },
  ]);
});
