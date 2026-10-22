import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Icon } from "./Icon";

export type ToastKind = "success" | "info" | "warning" | "danger";
interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}
type Notify = (kind: ToastKind, message: string, sticky?: boolean) => void;

const Ctx = createContext<Notify>(() => undefined);
export const useToast = (): Notify => useContext(Ctx);

const AUTO_HIDE_MS = 5000;

/** Thành công/thông tin tự ẩn sau 5 giây; lỗi và cảnh báo giữ lại tới khi người dùng đóng (Blueprint 2.5). */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const seq = useRef(0);

  const dismiss = useCallback((id: number) => setToasts((t) => t.filter((x) => x.id !== id)), []);
  const notify = useCallback<Notify>(
    (kind, message, sticky = false) => {
      const id = ++seq.current;
      setToasts((t) => [...t, { id, kind, message }]);
      if (!sticky && (kind === "success" || kind === "info"))
        setTimeout(() => dismiss(id), AUTO_HIDE_MS);
    },
    [dismiss],
  );
  const value = useMemo(() => notify, [notify]);

  return (
    <Ctx.Provider value={value}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast alert alert-${t.kind}`}>
            <Icon name={t.kind === "success" ? "check" : t.kind === "info" ? "info" : "alert"} />
            <span className="grow">{t.message}</span>
            <button
              className="btn btn-ghost btn-icon btn-sm"
              aria-label="Đóng thông báo"
              onClick={() => dismiss(t.id)}
            >
              <Icon name="x" />
            </button>
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
