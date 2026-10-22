import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ApiCitation, ApiDocument, AppConfig, ChatMessage, DataNotice } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { useTelemetry } from "../../telemetry/TelemetryProvider";
import { Icon } from "../../ui/Icon";
import { useToast } from "../../ui/Toasts";
import { Composer } from "../chat/Composer";
import { ChatPanel } from "../chat/ChatPanel";
import { composerState } from "../chat/composerState";
import { useChat } from "../chat/useChat";
import { citationLabel } from "../chat/MessageView";
import { DeleteDialog } from "../documents/DeleteDialog";
import { DocumentPanel } from "../documents/DocumentPanel";
import { useDocuments } from "../documents/useDocuments";
import { DataNoticeDialog } from "../notice/DataNoticeDialog";
import { SourcePanel } from "../source/SourcePanel";

const CONFIG_POLL_MS = 60_000; // nhận biết kill switch bật/tắt mà không cần tải lại trang
const DRAFT_KEY = "docchat.draft";

function readDraft(): string {
  try {
    return sessionStorage.getItem(DRAFT_KEY) ?? "";
  } catch {
    return "";
  }
}
function writeDraft(v: string): void {
  try {
    if (v) sessionStorage.setItem(DRAFT_KEY, v);
    else sessionStorage.removeItem(DRAFT_KEY);
  } catch {
    /* bỏ qua */
  }
}

export function Workspace({ trial = false }: { trial?: boolean }) {
  const { api, session, logout } = useAuth();
  const notify = useToast();
  const tracker = useTelemetry();

  const [config, setConfig] = useState<AppConfig | null>(null);
  const [notice, setNotice] = useState<DataNotice | null>(null);
  const [noticeOpen, setNoticeOpen] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [deleting, setDeleting] = useState<ApiDocument | null>(null);
  const [drawer, setDrawer] = useState(false);
  const [draft, setDraft] = useState(readDraft); // bản nháp sống sót qua hết phiên và tải lại trang (US-402)
  const [active, setActive] = useState<{
    key: string;
    index: number;
    citation: ApiCitation;
  } | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const lastTrigger = useRef<HTMLElement | null>(null);
  const [focusSignal, setFocusSignal] = useState(0);

  const loadConfig = useCallback(async () => {
    try {
      const c = await api.getConfig();
      setConfig(c);
      return c;
    } catch {
      return null;
    }
  }, [api]);

  // Tải cấu hình + thông báo; chưa xác nhận ⇒ mở cổng chặn (SCR-01).
  useEffect(() => {
    let alive = true;
    void (async () => {
      const c = await loadConfig();
      if (!alive || !c) return;
      const n = await api.getNotice().catch(() => null);
      if (!alive) return;
      setNotice(n);
      if (!c.noticeAccepted) setNoticeOpen(true);
    })();
    const t = setInterval(() => void loadConfig(), CONFIG_POLL_MS);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [api, loadConfig]);

  const docs = useDocuments(api, config, { onNoticeRequired: () => setNoticeOpen(true) });
  const selectedIds = useMemo(() => docs.selected.map((d) => d.id), [docs.selected]);
  const selectedRef = useRef(selectedIds);
  selectedRef.current = selectedIds;

  const chat = useChat({
    api,
    getDocumentIds: () => selectedRef.current,
    onKillSwitch: () => void loadConfig(),
    onDocumentsStale: () => void docs.refresh(),
  });

  // Quay lại tab (sau khi máy ngủ, đổi cửa sổ): làm mới ngay để phát hiện hết phiên / kill switch sớm.
  const refreshDocs = docs.refresh;
  useEffect(() => {
    const onFocus = () => {
      void refreshDocs();
      void loadConfig();
    };
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refreshDocs, loadConfig]);

  const known = useMemo(() => new Set(docs.docs.map((d) => d.id)), [docs.docs]);
  const noticeAccepted = config?.noticeAccepted ?? false;
  const qaEnabled = config?.qaEnabled ?? true;

  const composer = composerState({
    text: draft,
    noticeAccepted,
    qaEnabled,
    readyCount: docs.ready.length,
    selectedCount: docs.selected.length,
    maxQuestionLength: config?.maxQuestionLength ?? 2000,
    maxDocuments: config?.maxDocumentsPerQuestion ?? 10,
    streaming: chat.live,
  });

  const updateDraft = (v: string) => {
    setDraft(v);
    writeDraft(v);
  };

  const send = useCallback(
    (text: string) => {
      chat.ask(text);
      updateDraft("");
    },
    [chat],
  );

  // Thông báo cho trình đọc màn hình khi một câu trả lời hoàn tất
  const lastAi = [...chat.messages].reverse().find((m) => m.role === "ai");
  useEffect(() => {
    if (lastAi?.status === "complete") {
      const n = lastAi.citations.length;
      setAnnouncement(
        `Câu trả lời đã sẵn sàng${n ? `, có ${n} nguồn dẫn` : ", không có nguồn dẫn"}.`,
      );
    } else if (lastAi?.status === "failed" || lastAi?.status === "interrupted") {
      setAnnouncement("Không tạo được câu trả lời đầy đủ.");
    } else if (lastAi?.status === "stopped") {
      setAnnouncement("Đã dừng tạo câu trả lời.");
    }
  }, [lastAi?.status, lastAi?.citations.length]);

  // ---- nguồn dẫn ----
  const closeSource = useCallback(() => {
    setActive(null);
    const t = lastTrigger.current;
    if (t && document.contains(t)) t.focus();
    else document.querySelector<HTMLElement>(".chip")?.focus();
  }, []);

  const openSource = (m: ChatMessage, index: number, trigger: HTMLElement) => {
    if (active?.key === m.key && active.index === index) return closeSource();
    const citation = m.citations[index];
    if (!citation) return;
    lastTrigger.current = trigger;
    setActive({ key: m.key, index, citation });
    tracker.track("citation_opened", { citation_index: index });
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && active && !document.querySelector("dialog[open]")) closeSource();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [active, closeSource]);

  const copy = async (m: ChatMessage) => {
    const sources = m.citations.length
      ? `\n\nNguồn: ${m.citations.map(citationLabel).join("; ")}`
      : "";
    tracker.track("copy_answer", { answer_id: m.serverId ?? m.key });
    try {
      await navigator.clipboard.writeText(m.text + sources);
      notify("success", "Đã sao chép câu trả lời.");
    } catch {
      notify("danger", "Không sao chép được. Hãy chọn và sao chép thủ công.", true);
    }
  };

  const acceptNotice = async () => {
    if (!notice) return;
    setAccepting(true);
    try {
      await api.acceptNotice(notice.version);
      tracker.track("data_notice_accepted", { notice_version: notice.version });
      setNoticeOpen(false);
      await loadConfig();
      setFocusSignal((n) => n + 1);
    } catch {
      notify("danger", "Chưa ghi nhận được xác nhận. Hãy thử lại.", true);
    } finally {
      setAccepting(false);
    }
  };

  const initial = (session?.name ?? "?").trim().charAt(0).toUpperCase();
  const isEvaluator = session?.roles.includes("evaluator") ?? false;

  return (
    <div className="app">
      <a className="sr-only" href="#composer-input">
        Bỏ qua tới ô nhập câu hỏi
      </a>
      <header className="app-header">
        <button
          className="btn btn-ghost btn-icon menu-btn"
          aria-label="Mở danh sách tài liệu"
          aria-expanded={drawer}
          aria-controls="panel-docs"
          onClick={() => setDrawer((v) => !v)}
        >
          <Icon name="menu" />
        </button>
        <h1 className="title">Chat với tài liệu</h1>
        <span className="spacer" />
        {isEvaluator && (
          <a className="btn btn-sm header-link" href="#/report">
            Báo cáo
          </a>
        )}
        <button className="btn btn-sm" onClick={() => setNoticeOpen(true)}>
          <Icon name="info" />
          <span className="hide-sm">Thông báo dữ liệu</span>
        </button>
        <span className="user-chip">
          <span className="avatar" aria-hidden="true">
            {initial}
          </span>
          <span className="name">{session?.name}</span>
        </span>
        <button className="btn btn-sm btn-ghost" onClick={logout}>
          Đăng xuất
        </button>
      </header>

      <div className="global-banner" role="status">
        {!qaEnabled && (
          <div className="alert alert-danger">
            <Icon name="alert" />
            <span className="grow">
              <strong>Hỏi đáp tạm thời không khả dụng.</strong> Chúng tôi đang khắc phục. Tài liệu
              của bạn vẫn được giữ nguyên.
            </span>
          </div>
        )}
      </div>

      <main className={`workspace${active ? " source-open" : ""}`}>
        <DocumentPanel
          config={config}
          docs={docs.docs}
          uploads={docs.uploads}
          deselected={docs.deselected}
          noticeAccepted={noticeAccepted}
          open={drawer}
          onFiles={docs.addFiles}
          onToggle={docs.toggle}
          onDelete={setDeleting}
          onRetry={docs.retry}
          onCancel={docs.cancel}
          onDismissUpload={docs.dismissUpload}
        />
        {drawer && <div className="drawer-scrim" onClick={() => setDrawer(false)} />}

        <ChatPanel
          messages={chat.messages}
          hasReadyDocs={docs.ready.length > 0}
          canAsk={!composer.off && !composer.stop}
          activeCitation={active ? { key: active.key, index: active.index } : null}
          knownDocumentIds={known}
          announcement={announcement}
          onSuggest={send}
          onCite={openSource}
          onRetry={chat.retry}
          onCopy={copy}
          onRate={chat.rate}
        >
          <Composer
            state={composer}
            value={draft}
            maxLength={config?.maxQuestionLength ?? 2000}
            trial={trial}
            focusSignal={focusSignal}
            onChange={updateDraft}
            onSend={() => send(draft)}
            onStop={chat.stop}
            onTaskDone={chat.markTaskDone}
          />
        </ChatPanel>

        <SourcePanel
          citation={active?.citation ?? null}
          api={api}
          knownDocumentIds={known}
          onClose={closeSource}
        />
      </main>

      <DataNoticeDialog
        open={noticeOpen}
        review={noticeAccepted}
        notice={notice}
        busy={accepting}
        onAccept={() => void acceptNotice()}
        onClose={() => setNoticeOpen(false)}
      />
      <DeleteDialog
        doc={deleting}
        onCancel={() => setDeleting(null)}
        onConfirm={async (d) => {
          const ok = await docs.remove(d);
          if (ok) setDeleting(null);
          return ok;
        }}
      />
    </div>
  );
}
