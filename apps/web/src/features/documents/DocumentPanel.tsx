import { useRef, useState } from "react";
import type { ApiDocument, AppConfig } from "../../api/types";
import { Icon, type IconName } from "../../ui/Icon";
import { fmtAge, fmtSize } from "../../ui/format";
import type { LocalUpload } from "./useDocuments";
import { documentErrorAdvice, documentErrorText } from "./errors";

interface Props {
  config: AppConfig | null;
  docs: ApiDocument[];
  uploads: LocalUpload[];
  deselected: Set<string>;
  noticeAccepted: boolean;
  open: boolean; // drawer (< 1024px)
  onFiles(files: FileList | File[]): void;
  onToggle(id: string, on: boolean): void;
  onDelete(doc: ApiDocument): void;
  onRetry(id: string): void;
  onCancel(id: string): void;
  onDismissUpload(id: string): void;
}

interface Badge {
  cls: "info" | "success" | "warning" | "danger";
  icon: IconName;
  text: string;
}

// Trạng thái luôn có biểu tượng + chữ, không chỉ dựa vào màu (DD-07).
function docBadge(d: ApiDocument): Badge {
  if (d.status === "ready") return { cls: "success", icon: "check", text: "Sẵn sàng" };
  if (d.status === "error")
    return { cls: "danger", icon: "x", text: `Lỗi: ${documentErrorText(d.errorCode)}` };
  return { cls: "warning", icon: "clock", text: "Đang xử lý" };
}

/** SCR-02/SCR-03 — danh sách tài liệu, trạng thái và tải lên (US-101, US-102, US-104). */
export function DocumentPanel(p: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const total = p.docs.length + p.uploads.length;
  const pick = () => input.current?.click();

  return (
    <aside
      className={`panel panel-docs${p.open ? " open" : ""}`}
      id="panel-docs"
      aria-label="Tài liệu của tôi"
    >
      <div className="panel-head">
        <h2>Tài liệu của tôi ({total})</h2>
        <button className="btn btn-primary" onClick={pick} disabled={!p.noticeAccepted}>
          <Icon name="upload" />
          Tải PDF lên
        </button>
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          data-testid="file-input"
          onChange={(e) => {
            if (e.target.files?.length) p.onFiles(e.target.files);
            e.target.value = "";
          }}
        />
        {p.config && (
          <p className="doc-limit">
            Giới hạn: ≤ {fmtSize(p.config.maxFileSizeBytes)}/tệp, tối đa {p.config.maxFiles} tệp{" "}
            <span className="tbd">TBD: OQ-008</span>
          </p>
        )}
        {p.noticeAccepted && (
          <div
            className={`dropzone${drag ? " drag" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              p.onFiles(e.dataTransfer.files);
            }}
          >
            Hoặc kéo-thả PDF vào đây
          </div>
        )}
      </div>
      <div className="panel-scroll">
        {total === 0 && (
          <div className="empty">
            <div className="empty-art">
              <Icon name="file" />
            </div>
            <h3>Chưa có tài liệu</h3>
            <p>Tải PDF đầu tiên của bạn lên để bắt đầu đặt câu hỏi.</p>
            <button className="btn btn-primary" onClick={pick} disabled={!p.noticeAccepted}>
              <Icon name="upload" />
              Tải PDF đầu tiên
            </button>
          </div>
        )}
        <ul className="doc-list">
          {p.uploads.map((u) => (
            <li key={u.id} className="doc-item">
              <span className="checkbox-hit">
                <input
                  type="checkbox"
                  className="checkbox"
                  disabled
                  aria-label={`Dùng ${u.file.name} để hỏi đáp`}
                />
              </span>
              <div className="doc-main">
                <span className="doc-name" title={u.file.name}>
                  {u.file.name}
                </span>
                <span className="doc-meta">{fmtSize(u.file.size)}</span>
                <span>
                  <span className={`badge badge-${u.status === "uploading" ? "info" : "danger"}`}>
                    <Icon name={u.status === "uploading" ? "upload" : "alert"} />
                    {u.status === "uploading" ? `Đang tải lên… (${u.progress}%)` : "Tải thất bại"}
                  </span>
                </span>
                {u.status === "uploading" && (
                  <div
                    className="progress"
                    role="progressbar"
                    aria-label={`Tiến trình tải ${u.file.name}`}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={u.progress}
                  >
                    <span style={{ width: `${u.progress}%` }} />
                  </div>
                )}
                {u.error && <span className="doc-error">{u.error}</span>}
                <div className="doc-actions">
                  {u.status === "uploading" ? (
                    <button className="btn btn-sm" onClick={() => p.onCancel(u.id)}>
                      Hủy
                    </button>
                  ) : (
                    <>
                      {u.retryable && (
                        <button className="btn btn-sm" onClick={() => p.onRetry(u.id)}>
                          <Icon name="refresh" />
                          Thử lại
                        </button>
                      )}
                      <button className="btn btn-sm" onClick={() => p.onDismissUpload(u.id)}>
                        <Icon name="x" />
                        Bỏ qua
                      </button>
                    </>
                  )}
                </div>
              </div>
            </li>
          ))}
          {p.docs.map((d) => {
            const b = docBadge(d);
            const ready = d.status === "ready";
            return (
              <li key={d.id} className="doc-item" data-status={d.status}>
                <span className="checkbox-hit">
                  <input
                    type="checkbox"
                    className="checkbox"
                    disabled={!ready}
                    checked={ready && !p.deselected.has(d.id)}
                    aria-label={`Dùng ${d.name} để hỏi đáp`}
                    onChange={(e) => p.onToggle(d.id, e.target.checked)}
                  />
                </span>
                <div className="doc-main">
                  <span className="doc-name" title={d.name}>
                    {d.name}
                  </span>
                  <span className="doc-meta">
                    {fmtSize(d.sizeBytes)} · {fmtAge(d.uploadedAt)}
                    {d.pageCount ? ` · ${d.pageCount} trang` : ""}
                  </span>
                  <span>
                    <span className={`badge badge-${b.cls}`}>
                      <Icon name={b.icon} />
                      {b.text}
                    </span>
                  </span>
                  {d.status === "processing" && (
                    <div className="progress indeterminate" aria-hidden="true">
                      <span />
                    </div>
                  )}
                  {d.status === "error" && (
                    <span className="doc-error">{documentErrorAdvice(d.errorCode)}</span>
                  )}
                  {d.status !== "processing" && (
                    <div className="doc-actions">
                      <button
                        className="btn btn-sm"
                        aria-label={`Xóa ${d.name}`}
                        onClick={() => p.onDelete(d)}
                      >
                        <Icon name="trash" />
                        Xóa
                      </button>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </aside>
  );
}
