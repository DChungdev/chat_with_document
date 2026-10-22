import { useState } from "react";
import type { ApiDocument } from "../../api/types";
import { Icon } from "../../ui/Icon";
import { Modal } from "../../ui/Modal";

interface Props {
  doc: ApiDocument | null;
  onConfirm(doc: ApiDocument): Promise<boolean>;
  onCancel(): void;
}

/** SCR-06 — xác nhận xóa (US-103): menu → Xóa → Xác nhận = 2 thao tác. */
export function DeleteDialog({ doc, onConfirm, onCancel }: Props) {
  const [busy, setBusy] = useState(false);
  return (
    <Modal open={doc !== null} labelledBy="del-title" onClose={onCancel}>
      <div className="dialog-body">
        <h2 id="del-title" className="dialog-title">
          <span style={{ color: "var(--color-danger)", display: "inline-flex" }}>
            <Icon name="trash" />
          </span>
          Xóa tài liệu?
        </h2>
        <p>
          “<strong>{doc?.name}</strong>” sẽ bị xóa. Các chip trích dẫn trỏ tới tài liệu này sẽ hiển
          thị “Nguồn không còn khả dụng”.
        </p>
        <p className="muted" style={{ fontSize: "var(--text-sm)" }}>
          Thao tác này không thể hoàn tác. Nếu bạn tải nhầm tài liệu nhạy cảm, hãy xóa ngay và xem
          hướng dẫn báo cáo <span className="tbd">TBD: OQ-012</span>.
        </p>
      </div>
      <div className="dialog-actions">
        <button className="btn" onClick={onCancel} disabled={busy}>
          Hủy
        </button>
        <button
          className="btn btn-danger"
          disabled={busy}
          onClick={async () => {
            if (!doc) return;
            setBusy(true);
            const ok = await onConfirm(doc);
            setBusy(false);
            if (!ok) return; // giữ hộp thoại để thử lại
          }}
        >
          Xóa tài liệu
        </button>
      </div>
    </Modal>
  );
}
