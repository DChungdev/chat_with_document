import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { ChatMessage } from "../../api/types";
import { Icon } from "../../ui/Icon";
import { MessageView } from "./MessageView";

const SUGGESTIONS = [
  "Điều khoản thanh toán là gì?",
  "Thời gian bảo hành bao lâu?",
  "Tổng giá trị báo giá là bao nhiêu?",
];
const NEAR_BOTTOM_PX = 80;

interface Props {
  messages: ChatMessage[];
  hasReadyDocs: boolean;
  canAsk: boolean;
  activeCitation: { key: string; index: number } | null;
  knownDocumentIds: ReadonlySet<string>;
  announcement: string;
  onSuggest(q: string): void;
  onCite(message: ChatMessage, index: number, trigger: HTMLElement): void;
  onRetry(key: string): void;
  onCopy(message: ChatMessage): void;
  onRate(key: string, value: "up" | "down"): void;
  children: React.ReactNode; // composer
}

/** SCR-04 — khung chat: nhãn AI cố định, danh sách tin nhắn, cuộn thông minh (US-201, US-204). */
export function ChatPanel(p: Props) {
  const box = useRef<HTMLDivElement>(null);
  const stick = useRef(true);
  const [showJump, setShowJump] = useState(false);

  const onScroll = () => {
    const el = box.current;
    if (!el) return;
    const away = el.scrollHeight - el.scrollTop - el.clientHeight;
    stick.current = away < NEAR_BOTTOM_PX;
    setShowJump(away >= 120);
  };

  // Tin nhắn mới: chỉ tự cuộn nếu người dùng đang ở gần đáy — không giật khi họ đang đọc phần trên.
  useLayoutEffect(() => {
    const el = box.current;
    if (el && stick.current) el.scrollTop = el.scrollHeight;
    else if (el && p.messages.length) setShowJump(true);
  }, [p.messages]);

  useEffect(() => {
    if (p.messages.length === 0) stick.current = true;
  }, [p.messages.length]);

  return (
    <section className="panel panel-chat" aria-label="Khung chat">
      <div className="alert alert-info ai-banner" id="ai-banner">
        <Icon name="info" />
        <span className="grow">Câu trả lời do AI tạo, hãy kiểm tra nguồn trước khi sử dụng.</span>
      </div>
      <div
        ref={box}
        className="messages"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        tabIndex={0}
        aria-label="Hội thoại"
        onScroll={onScroll}
      >
        {p.messages.length === 0 ? (
          p.hasReadyDocs ? (
            <div className="empty">
              <div className="empty-art">
                <Icon name="sparkle" />
              </div>
              <h3>Bạn muốn hỏi gì?</h3>
              <p>Chọn một câu hỏi mẫu hoặc tự nhập câu hỏi.</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    className="btn suggestion"
                    disabled={!p.canAsk}
                    onClick={() => p.onSuggest(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty">
              <div className="empty-art">
                <Icon name="file" />
              </div>
              <h3>Hãy tải PDF để bắt đầu</h3>
              <p>
                Sau khi tài liệu ở trạng thái “Sẵn sàng”, bạn có thể đặt câu hỏi bằng tiếng Việt và
                nhận câu trả lời kèm nguồn dẫn.
              </p>
            </div>
          )
        ) : (
          p.messages.map((m) => (
            <MessageView
              key={m.key}
              message={m}
              activeCitation={p.activeCitation}
              knownDocumentIds={p.knownDocumentIds}
              onCite={p.onCite}
              onRetry={p.onRetry}
              onCopy={p.onCopy}
              onRate={p.onRate}
            />
          ))
        )}
      </div>
      {showJump && (
        <button
          className="btn btn-sm scroll-down"
          onClick={() => {
            const el = box.current;
            if (el) el.scrollTop = el.scrollHeight;
            stick.current = true;
            setShowJump(false);
          }}
        >
          <Icon name="arrowDown" />
          Có nội dung mới
        </button>
      )}
      {/* Thông báo cho trình đọc màn hình khi câu trả lời xong — không đọc từng token (E12). */}
      <div className="sr-only" role="status" aria-live="polite">
        {p.announcement}
      </div>
      {p.children}
    </section>
  );
}
