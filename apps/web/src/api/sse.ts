export interface SseEvent {
  name: string;
  data: unknown;
}

/** Tách một khối sự kiện SSE ("event: x\ndata: {...}"). Khối hỏng hoặc chỉ là chú thích thì bỏ qua. */
function parseBlock(block: string): SseEvent | null {
  let name = "message";
  const data: string[] = [];
  for (const raw of block.split(/\r?\n/)) {
    if (raw === "" || raw.startsWith(":")) continue; // dòng trống / chú thích
    const idx = raw.indexOf(":");
    const field = idx === -1 ? raw : raw.slice(0, idx);
    const value = idx === -1 ? "" : raw.slice(idx + 1).replace(/^ /, "");
    if (field === "event") name = value;
    else if (field === "data") data.push(value);
  }
  if (data.length === 0) return null;
  try {
    return { name, data: JSON.parse(data.join("\n")) };
  } catch {
    return null;
  }
}

/** Đọc luồng SSE từ `fetch` (POST nên không dùng EventSource). Đúng khi dữ liệu bị cắt tại bất kỳ byte nào. */
export async function* readSse(body: ReadableStream<Uint8Array>): AsyncGenerator<SseEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let m: RegExpExecArray | null;
      while ((m = /\r?\n\r?\n/.exec(buffer))) {
        const block = buffer.slice(0, m.index);
        buffer = buffer.slice(m.index + m[0].length);
        const ev = parseBlock(block);
        if (ev) yield ev;
      }
    }
    buffer += decoder.decode();
    const tail = parseBlock(buffer);
    if (tail) yield tail;
  } finally {
    reader.releaseLock?.();
  }
}
