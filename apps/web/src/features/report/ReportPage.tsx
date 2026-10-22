import { useEffect, useState } from "react";
import type { MetricLine, MvpReport } from "../../api/types";
import { ApiError } from "../../api/client";
import { useAuth } from "../../auth/AuthProvider";

const STATUS: Record<MetricLine["status"], { cls: string; text: (m: MetricLine) => string }> = {
  met: {
    cls: "success",
    text: (m) => `Đạt mục tiêu ${m.comparison === ">=" ? "≥" : "≤"} ${m.target}${m.unit}`,
  },
  not_met: {
    cls: "danger",
    text: (m) => `Chưa đạt ${m.comparison === ">=" ? "≥" : "≤"} ${m.target}${m.unit}`,
  },
  unknown: { cls: "neutral", text: () => "Chưa thể kết luận" },
};

function fmt(m: MetricLine): string {
  if (m.value === null) return "—";
  const v = m.id === "MET-001" ? `−${Math.abs(m.value)}` : String(m.value);
  return `${v.replace(".", ",")}${m.unit === "%" ? "%" : ` ${m.unit}`}`;
}

/** SCR-09 — báo cáo đánh giá MVP cho Minh (US-501). Chỉ số liệu tổng hợp, không có nội dung người dùng. */
export function ReportPage() {
  const { api } = useAuth();
  const [report, setReport] = useState<MvpReport | null>(null);
  const [error, setError] = useState<"forbidden" | "other" | null>(null);

  useEffect(() => {
    let alive = true;
    api.mvpReport().then(
      (r) => alive && setReport(r),
      (e: unknown) =>
        alive && setError(e instanceof ApiError && e.status === 403 ? "forbidden" : "other"),
    );
    return () => {
      alive = false;
    };
  }, [api]);

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>
            Báo cáo đánh giá MVP <span className="badge badge-neutral">SCR-09</span>
          </h1>
          <p>
            Dành cho Minh (US-501). Chỉ có số liệu tổng hợp — không có nội dung tài liệu hay câu
            hỏi.
          </p>
        </div>
        <a className="btn" href="#/">
          ← Quay lại ứng dụng
        </a>
      </header>

      {error === "forbidden" && (
        <div className="alert alert-warning" role="alert">
          <span className="grow">
            <strong>Bạn không có quyền xem báo cáo này.</strong> Báo cáo dành cho vai trò người đánh
            giá.
          </span>
        </div>
      )}
      {error === "other" && (
        <div className="alert alert-danger" role="alert">
          <span className="grow">Không tải được báo cáo. Hãy thử lại sau.</span>
        </div>
      )}
      {!report && !error && <p role="status">Đang tải báo cáo…</p>}

      {report && (
        <>
          {!report.conclusive && (
            <div className="alert alert-warning" role="note">
              <span className="grow">
                <strong>Chưa thể kết luận.</strong>
                <ul style={{ margin: "4px 0 0", paddingLeft: 20 }}>
                  {report.reasons.map((r) => (
                    <li key={r}>{r}</li>
                  ))}
                  {report.reasons.length === 0 && <li>Một số chỉ số chưa có đủ dữ liệu.</li>}
                </ul>
              </span>
            </div>
          )}

          <section className="section" aria-labelledby="rp-metrics">
            <h2 id="rp-metrics">Chỉ số chính</h2>
            <div className="grid grid-4">
              {report.metrics.map((m) => {
                const s = STATUS[m.status];
                return (
                  <div className="card" key={m.id} data-testid={`metric-${m.id}`}>
                    <div className="muted">
                      {m.id} · {m.label}
                    </div>
                    <div className="kpi">{fmt(m)}</div>
                    <span className={`badge badge-${s.cls}`}>{s.text(m)}</span>
                    <p className="muted" style={{ fontSize: "var(--text-sm)", margin: "8px 0 0" }}>
                      n = {m.sample}. {m.note}
                    </p>
                  </div>
                );
              })}
            </div>
            <p className="muted" style={{ fontSize: "var(--text-sm)" }}>
              Dữ liệu đầu vào: {report.inputs.sessions} phiên, {report.inputs.users} người dùng,{" "}
              {report.inputs.tasks} tác vụ, {report.inputs.answers} câu trả lời.
            </p>
          </section>

          <section className="section" aria-labelledby="rp-errors">
            <h2 id="rp-errors">Tỷ lệ lỗi theo bước</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Bước</th>
                    <th>Sự kiện telemetry</th>
                    <th>Lỗi / tổng</th>
                    <th>Tỷ lệ</th>
                    <th>Biểu đồ</th>
                  </tr>
                </thead>
                <tbody>
                  {report.errorRates.map((r) => (
                    <tr key={r.event}>
                      <td>{r.step}</td>
                      <td>
                        <code>{r.event}</code>
                      </td>
                      <td>
                        {r.failed} / {r.total}
                      </td>
                      <td>{r.rate === null ? "—" : `${String(r.rate).replace(".", ",")}%`}</td>
                      <td>
                        <div
                          className="progress"
                          style={{ minWidth: 160 }}
                          role="img"
                          aria-label={r.rate === null ? "chưa có dữ liệu" : `${r.rate}%`}
                        >
                          <span style={{ width: `${r.rate ?? 0}%` }} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="section" aria-labelledby="rp-funnel">
            <h2 id="rp-funnel">Phễu sử dụng (số phiên)</h2>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Sự kiện</th>
                    <th>Số phiên</th>
                  </tr>
                </thead>
                <tbody>
                  {report.funnel.map((f) => (
                    <tr key={f.event}>
                      <td>
                        <code>{f.event}</code>
                      </td>
                      <td>{f.sessions}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="section">
            <h2>Quyền riêng tư</h2>
            <div className="alert alert-info">
              Báo cáo chỉ dùng siêu dữ liệu (độ dài, số lượng, mã lỗi). Không có nội dung tài liệu
              hay câu hỏi.
            </div>
          </section>
        </>
      )}
    </main>
  );
}
