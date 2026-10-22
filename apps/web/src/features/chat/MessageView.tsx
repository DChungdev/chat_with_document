import type { ApiCitation, ChatMessage } from "../../api/types";
import { Icon } from "../../ui/Icon";

interface Props {
  message: ChatMessage;
  activeCitation: { key: string; index: number } | null;
  /** id tài liệu còn tồn tại trong danh sách hiện tại (chip tới tài liệu đã xóa bị gạch). */
  knownDocumentIds: ReadonlySet<string>;
  onCite(message: ChatMessage, index: number, trigger: HTMLElement): void;
  onRetry(key: string): void;
  onCopy(message: ChatMessage): void;
  onRate(key: string, value: "up" | "down"): void;
}

export function citationLabel(c: ApiCitation): string {
  return `${c.documentName ?? "Tài liệu đã xóa"} · tr.${c.page}`;
}

function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <div className="msg msg-user">
      <div className="msg-head">Bạn</div>
      <div className="bubble">{message.text}</div>
    </div>
  );
}

/** Tin nhắn AI: nhãn "Do AI tạo", trạng thái, chip trích dẫn, hành động (US-201…205, 301, 302, 502). */
export function MessageView(p: Props) {
  const m = p.message;
  if (m.role === "user") return <UserMessage message={m} />;

  const live = m.status === "sending" || m.status === "streaming";
  const retryBtn = (label: string) => (
    <button className="btn btn-sm" onClick={() => p.onRetry(m.key)}>
      <Icon name="refresh" />
      {label}
    </button>
  );

  return (
    <div className="msg msg-ai" data-testid="ai-message" data-status={m.status}>
      <div className="msg-head">
        <Icon name="sparkle" />
        Trợ lý AI <span className="badge badge-neutral">Do AI tạo</span>
      </div>
      <div
        className={`bubble${m.status === "complete" && m.grounded === false ? " not-grounded" : ""}`}
      >
        {m.status === "sending" ? (
          <>
            <div className="skeleton" style={{ width: "90%", marginBottom: 8 }} />
            <div className="skeleton" style={{ width: "65%" }} />
          </>
        ) : (
          <>
            {m.text}
            {m.status === "streaming" && <span className="cursor" aria-hidden="true" />}
          </>
        )}
      </div>

      {live && (
        <div className="msg-status">
          <span className="spinner" aria-hidden="true" />
          {m.status === "sending" ? "Đang tìm trong tài liệu…" : "Đang tạo câu trả lời…"}
        </div>
      )}
      {m.status === "interrupted" && (
        <div className="msg-status warning">
          <Icon name="alert" />
          {m.errorText ?? "Bị gián đoạn"} — phần đã nhận được vẫn được giữ lại.{" "}
          {retryBtn("Tạo lại")}
        </div>
      )}
      {m.status === "failed" && (
        <div className="msg-status danger" role="alert">
          <Icon name="alert" />
          {m.errorText ?? "Chưa thể tạo câu trả lời lúc này. Câu hỏi của bạn vẫn được giữ."}{" "}
          {m.errorCode !== "QA_DISABLED" && retryBtn("Thử lại")}
        </div>
      )}
      {m.status === "stopped" && (
        <div className="msg-status">
          <Icon name="stop" />
          Đã dừng. {retryBtn("Hỏi lại")}
        </div>
      )}

      {m.status === "complete" && (
        <>
          {m.citations.length > 0 && (
            <div className="chips" aria-label="Nguồn dẫn">
              {m.citations.map((c, i) => {
                const valid =
                  c.valid && (c.documentId === null || p.knownDocumentIds.has(c.documentId));
                const open = p.activeCitation?.key === m.key && p.activeCitation.index === i;
                return (
                  <button
                    key={c.id}
                    className={`chip${valid ? "" : " invalid"}`}
                    aria-expanded={open}
                    aria-controls="panel-source"
                    onClick={(e) => p.onCite(m, i, e.currentTarget)}
                  >
                    <Icon name="file" />
                    {citationLabel(c)}
                  </button>
                );
              })}
            </div>
          )}
          <div className="answer-actions">
            <button className="btn btn-sm btn-ghost" onClick={() => p.onCopy(m)}>
              <Icon name="copy" />
              Sao chép
            </button>
            <button
              className="btn btn-sm btn-ghost btn-icon"
              aria-label="Hữu ích"
              aria-pressed={m.feedback === "up"}
              disabled={!m.serverId}
              onClick={() => p.onRate(m.key, "up")}
            >
              <Icon name="up" />
            </button>
            <button
              className="btn btn-sm btn-ghost btn-icon"
              aria-label="Không hữu ích"
              aria-pressed={m.feedback === "down"}
              disabled={!m.serverId}
              onClick={() => p.onRate(m.key, "down")}
            >
              <Icon name="down" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
