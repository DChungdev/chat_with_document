import { useEffect, useLayoutEffect, useRef } from "react";
import { Icon } from "../../ui/Icon";
import type { ComposerState } from "./composerState";

interface Props {
  state: ComposerState;
  value: string;
  maxLength: number;
  trial: boolean;
  onChange(v: string): void;
  onSend(): void;
  onStop(): void;
  onTaskDone(success: boolean): void;
  focusSignal?: number;
}

/** Ô nhập câu hỏi (US-201). Enter gửi, Shift+Enter xuống dòng; không gửi khi đang gõ dấu bằng IME. */
export function Composer({
  state,
  value,
  maxLength,
  trial,
  onChange,
  onSend,
  onStop,
  onTaskDone,
  focusSignal,
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [value]);

  useEffect(() => {
    if (focusSignal) ref.current?.focus();
  }, [focusSignal]);

  const sendDisabled = Boolean(state.off || state.sendOff) && !state.stop;

  return (
    <div className="composer">
      <div className="composer-row">
        <label className="sr-only" htmlFor="composer-input">
          Câu hỏi của bạn
        </label>
        <textarea
          ref={ref}
          id="composer-input"
          rows={1}
          value={value}
          disabled={Boolean(state.off)}
          placeholder="Nhập câu hỏi về tài liệu…"
          aria-describedby="composer-hint composer-count"
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              if (!state.off && !state.sendOff && !state.stop) onSend();
            }
          }}
        />
        <button
          className="btn btn-primary"
          disabled={sendDisabled}
          aria-label={state.stop ? "Dừng tạo câu trả lời" : "Gửi câu hỏi"}
          onClick={state.stop ? onStop : onSend}
        >
          <Icon name={state.stop ? "stop" : "send"} />
          <span className="hide-sm">{state.stop ? "Dừng" : "Gửi"}</span>
        </button>
      </div>
      <div className="composer-meta">
        <span
          id="composer-hint"
          className="reason"
          role="status"
          style={state.neutral ? { color: "var(--text-muted)" } : undefined}
        >
          {state.reason ?? ""}
        </span>
        <span id="composer-count">
          {value.length}/{maxLength} · Shift+Enter xuống dòng
        </span>
      </div>
      {trial && (
        <div className="trial-bar">
          <button className="btn btn-sm" onClick={() => onTaskDone(true)}>
            <Icon name="check" />
            Tôi đã có thông tin cần tìm
          </button>{" "}
          <button className="btn btn-sm" onClick={() => onTaskDone(false)}>
            <Icon name="x" />
            Tôi không tìm được
          </button>
          <span className="muted" style={{ fontSize: "var(--text-sm)" }}>
            {" "}
            Chế độ thử nghiệm (OQ-005)
          </span>
        </div>
      )}
    </div>
  );
}
