import { useEffect, useRef, useState } from "react";
import type { Api } from "../../api/api";
import type { ApiCitation } from "../../api/types";
import { Icon } from "../../ui/Icon";

interface Props {
  citation: ApiCitation | null;
  api: Api;
  knownDocumentIds: ReadonlySet<string>;
  onClose(): void;
}

type Loaded = { state: "loading" } | { state: "ok"; data: ApiCitation } | { state: "error" };

/** SCR-05 — panel nguồn dẫn: đoạn gốc + tên tệp + trang, không rời trang (US-302, DD-01). */
export function SourcePanel({ citation, api, knownDocumentIds, onClose }: Props) {
  const [loaded, setLoaded] = useState<Loaded>({ state: "loading" });
  const closeBtn = useRef<HTMLButtonElement>(null);
  const open = citation !== null;

  useEffect(() => {
    if (!citation) return;
    let cancelled = false;
    setLoaded({ state: "loading" });
    api.getCitation(citation.id).then(
      (data) => !cancelled && setLoaded({ state: "ok", data }),
      () => !cancelled && setLoaded({ state: "error" }),
    );
    closeBtn.current?.focus();
    return () => {
      cancelled = true;
    };
  }, [citation, api]);

  const data = loaded.state === "ok" ? loaded.data : null;
  const available =
    data !== null &&
    data.valid &&
    Boolean(data.snippet) &&
    (data.documentId === null || knownDocumentIds.has(data.documentId));

  return (
    <aside
      className="panel panel-source"
      id="panel-source"
      aria-label="Nguồn dẫn"
      aria-hidden={!open}
    >
      <div className="panel-head">
        <div className="row" style={{ justifyContent: "space-between", flexWrap: "nowrap" }}>
          <h2>Nguồn dẫn</h2>
          <button ref={closeBtn} className="btn btn-sm" onClick={onClose} tabIndex={open ? 0 : -1}>
            <Icon name="x" />
            Đóng
          </button>
        </div>
      </div>
      <div className="source-body">
        {open && loaded.state === "loading" && (
          <>
            <div className="skeleton" style={{ width: "50%" }} />
            <div className="skeleton" style={{ height: 64 }} />
          </>
        )}
        {open && loaded.state === "error" && (
          <div className="alert alert-danger" role="alert">
            <Icon name="alert" />
            <span className="grow">Không tải được đoạn nguồn. Hãy thử lại.</span>
          </div>
        )}
        {open && data && available && (
          <>
            <div className="source-meta">
              <span className="badge badge-info">
                <Icon name="file" />
                {data.documentName}
              </span>
              <span className="badge badge-neutral">Trang {data.page}</span>
            </div>
            <blockquote className="source-quote">“{data.snippet}”</blockquote>
            <p className="muted" style={{ fontSize: "var(--text-sm)" }}>
              Đoạn gốc trích từ tài liệu bạn đã tải lên. Đối chiếu với câu trả lời trước khi sử
              dụng.
            </p>
          </>
        )}
        {open && data && !available && (
          <div className="alert alert-warning">
            <Icon name="alert" />
            <span className="grow">
              <strong>Nguồn không còn khả dụng.</strong>{" "}
              {citation?.documentName
                ? `Tài liệu “${citation.documentName}” đã bị xóa. `
                : "Tài liệu đã bị xóa. "}
              Tải lại tài liệu và hỏi lại nếu cần kiểm chứng.
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}
