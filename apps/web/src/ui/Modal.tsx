import { useEffect, useRef, type ReactNode } from "react";

interface Props {
  open: boolean;
  labelledBy: string;
  /** false: người dùng không thể đóng bằng Esc (cổng chặn thông báo dữ liệu, hết phiên). */
  dismissible?: boolean;
  onClose?: () => void;
  children: ReactNode;
}

/**
 * <dialog> gốc: trình duyệt tự bẫy focus, đóng bằng Esc và làm mờ nền. Lưu phần tử đang focus để trả
 * focus khi đóng (WCAG 2.4.3), kể cả môi trường không có showModal (jsdom).
 */
export function Modal({ open, labelledBy, dismissible = true, onClose, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const previous = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const dlg = ref.current;
    if (!dlg) return;
    if (open && !dlg.open) {
      previous.current = document.activeElement as HTMLElement | null;
      if (typeof dlg.showModal === "function") dlg.showModal();
      else dlg.setAttribute("open", "");
    } else if (!open && dlg.open) {
      if (typeof dlg.close === "function") dlg.close();
      else dlg.removeAttribute("open");
      previous.current?.focus?.();
    }
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={labelledBy}
      onCancel={(e) => {
        e.preventDefault(); // trạng thái do React quyết định, không phải trình duyệt
        if (dismissible) onClose?.();
      }}
    >
      {children}
    </dialog>
  );
}
