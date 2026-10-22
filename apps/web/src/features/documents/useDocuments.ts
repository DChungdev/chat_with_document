import { useCallback, useEffect, useRef, useState } from "react";
import type { Api } from "../../api/api";
import type { ApiDocument, AppConfig } from "../../api/types";
import { useTelemetry } from "../../telemetry/TelemetryProvider";
import { useToast } from "../../ui/Toasts";
import { fmtSize, uuid } from "../../ui/format";
import { documentErrorAdvice, documentErrorText, uploadErrorMessage } from "./errors";

export interface LocalUpload {
  id: string;
  file: File;
  idempotencyKey: string; // giữ nguyên khi thử lại để không tạo tài liệu trùng
  status: "uploading" | "upload_failed";
  progress: number;
  startedAt: number;
  error?: string;
  retryable?: boolean;
}

const POLL_FAST_MS = 2500; // khi còn tài liệu đang xử lý
const POLL_SLOW_MS = 30_000;
const UPLOAD_CONCURRENCY = 3; // API_Design 3.4.2

function isPdf(f: File): boolean {
  return f.type === "application/pdf" || /\.pdf$/i.test(f.name);
}

export function useDocuments(
  api: Api,
  config: AppConfig | null,
  opts: { onNoticeRequired(): void; pollMs?: number },
) {
  const notify = useToast();
  const tracker = useTelemetry();
  const [docs, setDocs] = useState<ApiDocument[]>([]);
  const [uploads, setUploads] = useState<LocalUpload[]>([]);
  const [deselected, setDeselected] = useState<Set<string>>(new Set()); // mặc định chọn mọi tài liệu sẵn sàng
  const [loaded, setLoaded] = useState(false);
  const seen = useRef<Map<string, ApiDocument["status"]>>(new Map());
  const controllers = useRef<Map<string, AbortController>>(new Map());
  const active = useRef(0);
  const queue = useRef<string[]>([]);
  const uploadsRef = useRef<LocalUpload[]>([]);
  uploadsRef.current = uploads;
  const configRef = useRef(config);
  configRef.current = config;

  const refresh = useCallback(async () => {
    try {
      const list = await api.listDocuments();
      // Phát telemetry khi quan sát thấy chuyển trạng thái processing → ready/error
      for (const d of list) {
        const before = seen.current.get(d.id);
        if (before === "processing" && d.status === "ready") {
          tracker.track("document_ready", {
            page_count: d.pageCount ?? 0,
            processing_ms: Math.max(0, Date.now() - Date.parse(d.uploadedAt)),
          });
          notify("success", `“${d.name}” đã sẵn sàng.`);
        } else if (before === "processing" && d.status === "error") {
          tracker.track("document_processing_failed", { error_code: d.errorCode ?? "UNKNOWN" });
          notify(
            "danger",
            `Không xử lý được “${d.name}”: ${documentErrorText(d.errorCode)}. ${documentErrorAdvice(d.errorCode)}`,
            true,
          );
        }
        seen.current.set(d.id, d.status);
      }
      setDocs(list);
      setLoaded(true);
    } catch {
      /* mất kết nối thoáng qua: lần polling sau sẽ thử lại */
    }
  }, [api, notify, tracker]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const anyProcessing =
    docs.some((d) => d.status === "processing") || uploads.some((u) => u.status === "uploading");
  useEffect(() => {
    const ms = opts.pollMs ?? (anyProcessing ? POLL_FAST_MS : POLL_SLOW_MS);
    const t = setInterval(() => void refresh(), ms);
    return () => clearInterval(t);
  }, [anyProcessing, refresh, opts.pollMs]);

  const patchUpload = (id: string, patch: Partial<LocalUpload>) =>
    setUploads((list) => list.map((u) => (u.id === id ? { ...u, ...patch } : u)));

  const runNext = useCallback(() => {
    while (active.current < UPLOAD_CONCURRENCY && queue.current.length) {
      const id = queue.current.shift() as string;
      const item = uploadsRef.current.find((u) => u.id === id);
      if (!item) continue;
      active.current += 1;
      const controller = new AbortController();
      controllers.current.set(id, controller);
      const startedAt = Date.now();
      patchUpload(id, { status: "uploading", progress: 0, error: undefined, startedAt });
      api
        .uploadDocument(
          item.file,
          item.idempotencyKey,
          (p) => patchUpload(id, { progress: p }),
          controller.signal,
        )
        .then((doc) => {
          tracker.track("upload_succeeded", {
            file_size: item.file.size,
            duration_ms: Date.now() - startedAt,
          });
          seen.current.set(doc.id, doc.status);
          setDocs((d) => (d.some((x) => x.id === doc.id) ? d : [doc, ...d]));
          setUploads((list) => list.filter((u) => u.id !== id));
        })
        .catch((e: unknown) => {
          if (e instanceof DOMException && e.name === "AbortError") return; // người dùng hủy
          const m = uploadErrorMessage(e, item.file.name, configRef.current?.maxFileSizeBytes ?? 0);
          const code = (e as { code?: string }).code ?? "NETWORK_ERROR";
          tracker.track("upload_failed", { file_size: item.file.size, error_code: code });
          if (code === "NOTICE_NOT_ACCEPTED") opts.onNoticeRequired();
          patchUpload(id, { status: "upload_failed", error: m.text, retryable: m.retryable });
          notify("danger", m.text, true);
        })
        .finally(() => {
          controllers.current.delete(id);
          active.current -= 1;
          runNext();
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, notify, tracker]);

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      const cfg = configRef.current;
      if (!cfg) return;
      if (!cfg.noticeAccepted) {
        notify("warning", "Hãy xác nhận thông báo dữ liệu trước khi tải tài liệu.");
        opts.onNoticeRequired();
        return;
      }
      let count = docs.length + uploadsRef.current.length;
      const accepted: LocalUpload[] = [];
      Array.from(files).forEach((file, i) => {
        if (!isPdf(file))
          return notify("danger", `“${file.name}” không phải PDF. Hiện chỉ hỗ trợ tệp .pdf.`, true);
        if (file.size > cfg.maxFileSizeBytes) {
          return notify(
            "danger",
            `“${file.name}” vượt giới hạn ${fmtSize(cfg.maxFileSizeBytes)}. Hãy chọn tệp nhỏ hơn.`,
            true,
          );
        }
        if (count >= cfg.maxFiles)
          return notify(
            "danger",
            `Đã đạt tối đa ${cfg.maxFiles} tài liệu. Xóa bớt để tải thêm.`,
            true,
          );
        count += 1;
        tracker.track("upload_started", { file_size: file.size, file_index: i });
        accepted.push({
          id: uuid(),
          file,
          idempotencyKey: uuid(),
          status: "uploading",
          progress: 0,
          startedAt: Date.now(),
        });
      });
      if (!accepted.length) return;
      uploadsRef.current = [...accepted, ...uploadsRef.current];
      setUploads((list) => [...accepted, ...list]);
      queue.current.push(...accepted.map((a) => a.id));
      runNext();
    },
    [docs.length, notify, opts, runNext, tracker],
  );

  const retry = useCallback(
    (id: string) => {
      queue.current.push(id);
      patchUpload(id, { status: "uploading", progress: 0, error: undefined });
      runNext();
    },
    [runNext],
  );

  const cancel = useCallback(
    (id: string) => {
      controllers.current.get(id)?.abort();
      queue.current = queue.current.filter((q) => q !== id);
      const name = uploadsRef.current.find((u) => u.id === id)?.file.name ?? "";
      setUploads((list) => list.filter((u) => u.id !== id));
      notify("info", `Đã hủy tải “${name}”.`);
    },
    [notify],
  );

  const dismissUpload = useCallback(
    (id: string) => setUploads((list) => list.filter((u) => u.id !== id)),
    [],
  );

  const remove = useCallback(
    async (doc: ApiDocument): Promise<boolean> => {
      try {
        await api.deleteDocument(doc.id);
      } catch {
        notify("danger", `Chưa xóa được “${doc.name}”. Hãy thử lại.`, true);
        return false;
      }
      tracker.track("document_deleted", {
        document_age_days: Math.max(
          0,
          Math.floor((Date.now() - Date.parse(doc.uploadedAt)) / 86_400_000),
        ),
      });
      seen.current.delete(doc.id);
      setDocs((list) => list.filter((d) => d.id !== doc.id));
      notify("success", `Đã xóa “${doc.name}”.`);
      return true;
    },
    [api, notify, tracker],
  );

  const toggle = useCallback(
    (id: string, on: boolean) =>
      setDeselected((s) => {
        const next = new Set(s);
        if (on) next.delete(id);
        else next.add(id);
        return next;
      }),
    [],
  );

  const ready = docs.filter((d) => d.status === "ready");
  const selected = ready.filter((d) => !deselected.has(d.id));

  return {
    docs,
    uploads,
    loaded,
    ready,
    selected,
    deselected,
    addFiles,
    retry,
    cancel,
    dismissUpload,
    remove,
    toggle,
    refresh,
  };
}
