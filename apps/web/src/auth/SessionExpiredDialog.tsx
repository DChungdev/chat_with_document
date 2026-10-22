import { useState, type FormEvent } from "react";
import { Modal } from "../ui/Modal";
import { Icon } from "../ui/Icon";
import { useAuth } from "./AuthProvider";
import { useToast } from "../ui/Toasts";

/**
 * SCR-07: phiên hết hạn. Hiện đè lên màn hình đang dùng nên bản nháp câu hỏi và các tài liệu đã tải
 * vẫn nguyên (US-402). Không đóng được bằng Esc.
 */
export function SessionExpiredDialog() {
  const { expired, session, login } = useAuth();
  const notify = useToast();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function relogin(e: FormEvent) {
    e.preventDefault();
    if (!session) return;
    setBusy(true);
    setError(null);
    try {
      await login(session.name, session.roles.filter((r) => r !== "user").concat("user"));
      notify("success", "Đã đăng nhập lại. Câu hỏi đang soạn được giữ nguyên.");
    } catch {
      setError("Chưa đăng nhập lại được. Hãy thử lại.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal open={expired} labelledBy="ses-title" dismissible={false}>
      <form onSubmit={relogin}>
        <div className="dialog-body">
          <h2 id="ses-title" className="dialog-title">
            <Icon name="lock" />
            Phiên làm việc đã hết hạn
          </h2>
          <p>
            Vì lý do bảo mật, vui lòng đăng nhập lại để tiếp tục. Câu hỏi bạn đang soạn vẫn được giữ
            lại.
          </p>
          <p className="muted" style={{ fontSize: "var(--text-sm)" }}>
            Cơ chế đăng nhập <span className="tbd">TBD: OQ-014</span> — khung trung lập.
          </p>
          {error && (
            <div className="alert alert-danger" role="alert">
              <span className="grow">{error}</span>
            </div>
          )}
        </div>
        <div className="dialog-actions">
          <button className="btn btn-primary" type="submit" disabled={busy} autoFocus>
            Đăng nhập lại
          </button>
        </div>
      </form>
    </Modal>
  );
}
