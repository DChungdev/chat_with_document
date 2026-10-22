import { useEffect, useState } from "react";
import type { DataNotice } from "../../api/types";
import { Icon } from "../../ui/Icon";
import { Modal } from "../../ui/Modal";

interface Props {
  open: boolean;
  /** true: xem lại thông báo đã xác nhận (chỉ đọc, có nút Đóng). false: cổng chặn bắt buộc xác nhận. */
  review: boolean;
  notice: DataNotice | null;
  busy?: boolean;
  onAccept(): void;
  onClose(): void;
}

/** SCR-01 — Màn chào + thông báo dữ liệu (US-401). Không đóng được bằng Esc khi chưa xác nhận. */
export function DataNoticeDialog({ open, review, notice, busy = false, onAccept, onClose }: Props) {
  const [checked, setChecked] = useState(false);
  useEffect(() => setChecked(review), [review, open]);

  return (
    <Modal open={open} labelledBy="notice-title" dismissible={review} onClose={onClose}>
      <div className="dialog-body">
        <h2 id="notice-title" className="dialog-title">
          <Icon name="sparkle" />
          Chào mừng đến “Chat với tài liệu”
        </h2>
        <ul className="notice-list">
          <li>Hỏi đáp bằng tiếng Việt trên các PDF do bạn tải lên.</li>
          <li>Mỗi câu trả lời đều kèm nguồn dẫn để bạn kiểm chứng.</li>
        </ul>
        <div className="notice-box">
          <strong>Lưu ý về dữ liệu</strong> <span className="tbd">TBD: OQ-012/013</span>
          <ul className="notice-list" style={{ marginTop: 8 }}>
            <li>Chỉ tải tài liệu bạn có quyền sử dụng.</li>
            <li>Tài liệu và câu hỏi của bạn chỉ hiển thị cho riêng bạn.</li>
            <li>Bạn có thể xóa tài liệu bất cứ lúc nào (tối đa 2 thao tác).</li>
            <li>
              Thời hạn lưu trữ và cách xử lý dữ liệu:{" "}
              <span className="tbd">sẽ cập nhật khi được duyệt</span>
            </li>
          </ul>
          {notice?.content && <p style={{ marginTop: 8, marginBottom: 0 }}>{notice.content}</p>}
        </div>
        <label className="check-row">
          <input
            type="checkbox"
            className="checkbox"
            checked={checked}
            disabled={review}
            onChange={(e) => setChecked(e.target.checked)}
          />
          <span>Tôi đã đọc và đồng ý với thông báo dữ liệu.</span>
        </label>
      </div>
      <div className="dialog-actions">
        {review ? (
          <button className="btn btn-ghost" onClick={onClose}>
            Đóng
          </button>
        ) : (
          <button className="btn btn-primary" disabled={!checked || busy} onClick={onAccept}>
            Tiếp tục
          </button>
        )}
      </div>
    </Modal>
  );
}
