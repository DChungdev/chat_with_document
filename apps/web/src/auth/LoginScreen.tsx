import { useState, type FormEvent } from "react";
import { ApiError, NetworkError } from "../api/client";
import { useAuth } from "./AuthProvider";

const ROLES = [
  { value: "user", label: "Người dùng (Lan)" },
  { value: "evaluator", label: "Người đánh giá (Minh) — xem báo cáo" },
  { value: "ops", label: "Vận hành — bật/tắt hỏi đáp" },
];

/** Khung đăng nhập trung lập cho DEV [TBD: OQ-014]. */
export function LoginScreen({ initialName = "" }: { initialName?: string }) {
  const { login } = useAuth();
  const [name, setName] = useState(initialName);
  const [role, setRole] = useState("user");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(name.trim(), role === "user" ? ["user"] : ["user", role]);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError(
          "Máy chủ không bật đăng nhập thử nghiệm. Cơ chế đăng nhập chính thức chưa được cấu hình (OQ-014).",
        );
      } else if (err instanceof NetworkError) {
        setError("Không kết nối được máy chủ. Hãy kiểm tra máy chủ đang chạy.");
      } else if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError("Không đăng nhập được.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login">
      <h1>Chat với tài liệu</h1>
      <form className="card" onSubmit={submit} aria-labelledby="login-title">
        <h2 id="login-title">Đăng nhập</h2>
        <div className="alert alert-info">
          <span className="grow">
            Đăng nhập thử nghiệm cho môi trường phát triển. Cơ chế đăng nhập chính thức{" "}
            <span className="tbd">TBD: OQ-014</span>.
          </span>
        </div>
        <div>
          <label className="field-label" htmlFor="login-name">
            Tên của bạn
          </label>
          <input
            id="login-name"
            className="input"
            value={name}
            maxLength={40}
            required
            autoFocus
            autoComplete="username"
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <label className="field-label" htmlFor="login-role">
            Vai trò
          </label>
          <select
            id="login-role"
            className="select"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </div>
        {error && (
          <div className="alert alert-danger" role="alert">
            <span className="grow">{error}</span>
          </div>
        )}
        <button className="btn btn-primary" type="submit" disabled={busy || !name.trim()}>
          {busy ? "Đang đăng nhập…" : "Đăng nhập"}
        </button>
      </form>
    </main>
  );
}
