import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { describe, expect, it, vi } from "vitest";
import { ApiError } from "../../api/client";
import { CONFIG, doc, ev, fakeApi, sse } from "../../test/fakeApi";
import { renderApp } from "../../test/render";
import { Workspace } from "./Workspace";

const pdf = (name = "moi.pdf") => new File(["%PDF-1.4"], name, { type: "application/pdf" });

const answerStream = () =>
  sse([
    ev("message", { messageId: "srv1" }),
    ev("token", { text: "Thanh toán 30 ngày." }),
    ev("citations", {
      citations: [{ id: "c1", documentId: "d1", documentName: "baogia.pdf", page: 4, valid: true }],
    }),
    ev("done", { messageId: "srv1", status: "complete", grounded: true, citationCount: 1 }),
  ]);

function ready(over = {}) {
  return fakeApi({
    listDocuments: vi.fn(async () => [doc()]),
    ask: vi.fn(async () => answerStream()),
    ...over,
  });
}

async function ask(text: string) {
  const user = userEvent.setup();
  const box = await screen.findByLabelText("Câu hỏi của bạn");
  await waitFor(() => expect(box).toBeEnabled());
  await user.type(box, text + "{Enter}");
  return user;
}

describe("Workspace — trạng thái ban đầu", () => {
  it("chưa xác nhận thông báo ⇒ cổng chặn mở, tải lên và ô chat bị khóa", async () => {
    const api = fakeApi({ getConfig: vi.fn(async () => ({ ...CONFIG, noticeAccepted: false })) });
    renderApp(<Workspace />, { api });
    const dlg = await screen.findByRole("dialog", { name: /Chào mừng/ });
    expect(dlg).toHaveAttribute("open");
    expect(within(dlg).getByRole("button", { name: "Tiếp tục" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Tải PDF lên" })).toBeDisabled();
    expect(screen.getByLabelText("Câu hỏi của bạn")).toBeDisabled();
    expect(screen.getByText("Xác nhận thông báo dữ liệu để bắt đầu")).toBeInTheDocument();
  });

  it("tích đồng ý ⇒ gọi acceptNotice(version), phát telemetry và mở khóa", async () => {
    let accepted = false;
    const api = fakeApi({
      getConfig: vi.fn(async () => ({ ...CONFIG, noticeAccepted: accepted })),
      acceptNotice: vi.fn(async () => void (accepted = true)),
    });
    const { tracker } = renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    const dlg = await screen.findByRole("dialog", { name: /Chào mừng/ });
    await user.click(within(dlg).getByRole("checkbox"));
    await user.click(within(dlg).getByRole("button", { name: "Tiếp tục" }));
    await waitFor(() => expect(dlg).not.toHaveAttribute("open"));
    expect(api.acceptNotice).toHaveBeenCalledWith("v1");
    expect(tracker.events).toContainEqual({
      name: "data_notice_accepted",
      props: { notice_version: "v1" },
    });
    await waitFor(() => expect(screen.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled());
  });

  it("đã xác nhận ⇒ không có cổng; trạng thái rỗng hướng dẫn tải PDF", async () => {
    renderApp(<Workspace />, { api: fakeApi() });
    expect(await screen.findByText("Hãy tải PDF để bắt đầu")).toBeInTheDocument();
    expect(document.querySelector("dialog[aria-labelledby='notice-title']")).not.toHaveAttribute(
      "open",
    );
    expect(screen.getByText("Tải ít nhất 1 PDF và chờ ở trạng thái Sẵn sàng")).toBeInTheDocument();
    expect(screen.getByText(/Câu trả lời do AI tạo/)).toBeInTheDocument(); // nhãn AI cố định
  });

  it("kill switch: banner, ô chat khóa, tài liệu vẫn tải được", async () => {
    const api = ready({ getConfig: vi.fn(async () => ({ ...CONFIG, qaEnabled: false })) });
    renderApp(<Workspace />, { api });
    expect(await screen.findByText(/Hỏi đáp tạm thời không khả dụng\./)).toBeInTheDocument();
    expect(screen.getByLabelText("Câu hỏi của bạn")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled();
  });
});

describe("Workspace — hỏi đáp và nguồn dẫn", () => {
  it("hỏi → câu trả lời + chip → mở panel nguồn → Esc đóng và trả focus", async () => {
    const api = ready();
    const { tracker } = renderApp(<Workspace />, { api });
    const user = await ask("Hạn thanh toán?");

    const msg = await screen.findByTestId("ai-message");
    await waitFor(() => expect(msg).toHaveAttribute("data-status", "complete"));
    expect(within(msg).getByText("Do AI tạo")).toBeInTheDocument();
    const chip = within(msg).getByRole("button", { name: /baogia\.pdf · tr\.4/ });
    expect(screen.getByLabelText("Câu hỏi của bạn")).toHaveValue(""); // đã gửi ⇒ xóa ô nhập
    expect(window.sessionStorage.getItem("docchat.draft")).toBeNull();

    await user.click(chip);
    const panel = screen.getByRole("complementary", { name: "Nguồn dẫn" });
    expect((await within(panel).findAllByText(/Đoạn gốc/)).length).toBeGreaterThan(0);
    expect(api.getCitation).toHaveBeenCalledWith("c1");
    expect(chip).toHaveAttribute("aria-expanded", "true");
    expect(tracker.events).toContainEqual({
      name: "citation_opened",
      props: { citation_index: 0 },
    });

    await user.keyboard("{Escape}");
    await waitFor(() => expect(chip).toHaveAttribute("aria-expanded", "false"));
    expect(chip).toHaveFocus();
  });

  it("Enter gửi, Shift+Enter xuống dòng, không gửi khi rỗng", async () => {
    const api = ready();
    renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    const box = await screen.findByLabelText("Câu hỏi của bạn");
    await waitFor(() => expect(box).toBeEnabled());
    await user.type(box, "dòng một{Shift>}{Enter}{/Shift}dòng hai");
    expect(box).toHaveValue("dòng một\ndòng hai");
    expect(api.ask).not.toHaveBeenCalled();
    await user.clear(box);
    await user.type(box, "{Enter}");
    expect(api.ask).not.toHaveBeenCalled();
  });

  it("giữ bản nháp trong sessionStorage để sống sót qua hết phiên / tải lại", async () => {
    renderApp(<Workspace />, { api: ready() });
    const user = userEvent.setup();
    const box = await screen.findByLabelText("Câu hỏi của bạn");
    await waitFor(() => expect(box).toBeEnabled());
    await user.type(box, "câu đang soạn");
    expect(window.sessionStorage.getItem("docchat.draft")).toBe("câu đang soạn");
  });

  it("quá độ dài: khóa Gửi kèm lý do", async () => {
    renderApp(<Workspace />, {
      api: ready({ getConfig: vi.fn(async () => ({ ...CONFIG, maxQuestionLength: 10 })) }),
    });
    const user = userEvent.setup();
    const box = await screen.findByLabelText("Câu hỏi của bạn");
    await waitFor(() => expect(box).toBeEnabled());
    await user.type(box, "mười một ký tự");
    expect(screen.getByText("Tối đa 10 ký tự")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Gửi câu hỏi" })).toBeDisabled();
  });

  it("câu hỏi mẫu gửi ngay khi bấm", async () => {
    const api = ready();
    renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Điều khoản thanh toán là gì?" }));
    await waitFor(() => expect(api.ask).toHaveBeenCalled());
    expect((api.ask.mock.calls[0] as [string, { question: string }])[1].question).toBe(
      "Điều khoản thanh toán là gì?",
    );
  });

  it("chỉ gửi các tài liệu đang được chọn; bỏ chọn hết ⇒ khóa ô chat", async () => {
    const api = ready({
      listDocuments: vi.fn(async () => [
        doc({ id: "d1", name: "a.pdf" }),
        doc({ id: "d2", name: "b.pdf" }),
      ]),
    });
    renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    await user.click(await screen.findByRole("checkbox", { name: "Dùng a.pdf để hỏi đáp" }));
    await ask("q");
    await waitFor(() => expect(api.ask).toHaveBeenCalled());
    expect((api.ask.mock.calls[0] as [string, { documentIds: string[] }])[1].documentIds).toEqual([
      "d2",
    ]);
    await user.click(screen.getByRole("checkbox", { name: "Dùng b.pdf để hỏi đáp" }));
    expect(screen.getByLabelText("Câu hỏi của bạn")).toBeDisabled();
    expect(screen.getByText("Chọn ít nhất 1 tài liệu để hỏi")).toBeInTheDocument();
  });

  it("chip tới tài liệu đã xóa bị gạch và panel báo không còn khả dụng", async () => {
    const api = ready({
      getCitation: vi.fn(async () => ({
        id: "c1",
        documentId: null,
        documentName: null,
        page: 4,
        snippet: null,
        valid: false,
      })),
    });
    renderApp(<Workspace />, { api });
    const user = await ask("q");
    const msg = await screen.findByTestId("ai-message");
    await waitFor(() => expect(msg).toHaveAttribute("data-status", "complete"));
    await user.click(within(msg).getByRole("button", { name: /baogia\.pdf/ }));
    expect(await screen.findByText("Nguồn không còn khả dụng.")).toBeInTheDocument();
  });

  it("sao chép: chép câu trả lời kèm nguồn vào clipboard", async () => {
    renderApp(<Workspace />, { api: ready() });
    const user = await ask("q");
    const msg = await screen.findByTestId("ai-message");
    await waitFor(() => expect(msg).toHaveAttribute("data-status", "complete"));
    await user.click(within(msg).getByRole("button", { name: "Sao chép" }));
    expect(await navigator.clipboard.readText()).toBe(
      "Thanh toán 30 ngày." + String.fromCharCode(10, 10) + "Nguồn: baogia.pdf · tr.4",
    );
  });

  it("đánh giá hữu ích gọi API và đánh dấu aria-pressed", async () => {
    const api = ready();
    renderApp(<Workspace />, { api });
    const user = await ask("q");
    const msg = await screen.findByTestId("ai-message");
    await waitFor(() => expect(msg).toHaveAttribute("data-status", "complete"));
    const up = within(msg).getByRole("button", { name: "Hữu ích" });
    await user.click(up);
    expect(api.sendFeedback).toHaveBeenCalledWith("srv1", "up");
    expect(up).toHaveAttribute("aria-pressed", "true");
  });

  it("trình đọc màn hình được báo khi xong (không đọc từng token)", async () => {
    renderApp(<Workspace />, { api: ready() });
    await ask("q");
    expect(await screen.findByText("Câu trả lời đã sẵn sàng, có 1 nguồn dẫn.")).toBeInTheDocument();
    const log = screen.getByRole("log", { name: "Hội thoại" });
    expect(log).toHaveAttribute("aria-relevant", "additions");
  });
});

describe("Workspace — XSS", () => {
  it("văn bản câu trả lời/tên tệp chứa HTML được hiển thị như chữ, không thành phần tử", async () => {
    const evil = '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>';
    const api = fakeApi({
      listDocuments: vi.fn(async () => [doc({ name: evil })]),
      ask: vi.fn(async () =>
        sse([
          ev("message", { messageId: "s" }),
          ev("token", { text: evil }),
          ev("done", { messageId: "s", status: "complete", grounded: false, citationCount: 0 }),
        ]),
      ),
    });
    const { container } = renderApp(<Workspace />, { api });
    await ask("q");
    const msg = await screen.findByTestId("ai-message");
    await waitFor(() => expect(msg).toHaveAttribute("data-status", "complete"));
    expect(container.querySelector("img[src='x'], script")).toBeNull();
    expect(msg.textContent).toContain("<img src=x");
    expect((window as unknown as { __xss?: number }).__xss).toBeUndefined();
  });
});

describe("Workspace — tài liệu", () => {
  it("tải PDF: kiểm tra phía client (loại, kích thước) trước khi gọi API", async () => {
    const api = fakeApi({ getConfig: vi.fn(async () => ({ ...CONFIG, maxFileSizeBytes: 10 })) });
    renderApp(<Workspace />, { api });
    const user = userEvent.setup({ applyAccept: false });
    const input = await screen.findByTestId("file-input");
    await waitFor(() => expect(screen.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled());
    await user.upload(input, new File(["abc"], "ghi-chu.txt", { type: "text/plain" }));
    expect(await screen.findByText(/không phải PDF/)).toBeInTheDocument();
    await user.upload(input, new File(["x".repeat(50)], "lon.pdf", { type: "application/pdf" }));
    expect(await screen.findByText(/vượt giới hạn/)).toBeInTheDocument();
    expect(api.uploadDocument).not.toHaveBeenCalled();
  });

  it("tải lên thành công: có tiến trình, rồi xuất hiện trong danh sách; telemetry không chứa tên tệp", async () => {
    const api = fakeApi({
      uploadDocument: vi.fn(async (f: File, _k: string, onProgress: (p: number) => void) => {
        onProgress(60);
        return doc({ id: "n1", name: f.name, status: "processing", pageCount: null });
      }),
    });
    const { tracker } = renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    await waitFor(() => expect(screen.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled());
    await user.upload(await screen.findByTestId("file-input"), pdf("hopdong.pdf"));
    expect(await screen.findByText("hopdong.pdf")).toBeInTheDocument();
    expect(await screen.findByText("Đang xử lý")).toBeInTheDocument();
    const names = tracker.events.map((e) => e.name);
    expect(names).toContain("upload_started");
    expect(names).toContain("upload_succeeded");
    expect(JSON.stringify(tracker.events)).not.toContain("hopdong");
    expect((api.uploadDocument.mock.calls[0] as [File, string])[1]).toMatch(/^[0-9a-f-]{36}$/); // Idempotency-Key
  });

  it("tải lên lỗi: nêu lý do, có Thử lại (cùng Idempotency-Key) khi lỗi tạm thời", async () => {
    const upload = vi
      .fn()
      .mockRejectedValueOnce(new ApiError({ title: "x", status: 429, code: "RATE_LIMITED" }, 8))
      .mockResolvedValue(doc({ id: "n1", name: "a.pdf", status: "processing", pageCount: null }));
    const api = fakeApi({ uploadDocument: upload });
    renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    await waitFor(() => expect(screen.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled());
    await user.upload(await screen.findByTestId("file-input"), pdf("a.pdf"));
    expect(await screen.findAllByText(/quá nhanh, thử lại sau 8 giây/)).not.toHaveLength(0);
    expect(screen.getByText("Tải thất bại")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Thử lại/ }));
    await waitFor(() => expect(screen.queryByText("Tải thất bại")).not.toBeInTheDocument());
    expect(upload).toHaveBeenCalledTimes(2);
    expect(upload.mock.calls[1]?.[1]).toBe(upload.mock.calls[0]?.[1]);
  });

  it("trạng thái luôn có chữ + biểu tượng; tài liệu lỗi có lý do và không chọn được", async () => {
    const api = fakeApi({
      listDocuments: vi.fn(async () => [
        doc({ id: "r", name: "ok.pdf" }),
        doc({ id: "p", name: "dang.pdf", status: "processing", pageCount: null }),
        doc({
          id: "e",
          name: "mk.pdf",
          status: "error",
          errorCode: "PDF_PASSWORD",
          pageCount: null,
        }),
        doc({ id: "s", name: "scan.pdf", status: "error", errorCode: "NO_TEXT", pageCount: null }),
      ]),
    });
    renderApp(<Workspace />, { api });
    expect(await screen.findByText("Sẵn sàng")).toBeInTheDocument();
    expect(screen.getByText("Đang xử lý")).toBeInTheDocument();
    expect(screen.getByText("Lỗi: PDF có mật khẩu")).toBeInTheDocument();
    expect(screen.getByText("Lỗi: PDF quét, không có chữ để đọc")).toBeInTheDocument();
    expect(screen.getByText("Hãy gỡ mật khẩu rồi tải lại.")).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Dùng mk.pdf để hỏi đáp" })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: "Dùng dang.pdf để hỏi đáp" })).toBeDisabled();
    expect(screen.getByRole("checkbox", { name: "Dùng ok.pdf để hỏi đáp" })).toBeChecked();
  });

  it("xóa: hộp xác nhận, Hủy không xóa, Xác nhận gọi API và cập nhật danh sách", async () => {
    const api = ready();
    const { tracker } = renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Xóa baogia.pdf" }));
    const dlg = screen.getByRole("dialog", { name: "Xóa tài liệu?" });
    expect(dlg).toHaveAttribute("open");
    await user.click(within(dlg).getByRole("button", { name: "Hủy" }));
    expect(api.deleteDocument).not.toHaveBeenCalled();
    expect(screen.getByText("baogia.pdf")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Xóa baogia.pdf" }));
    await user.click(within(dlg).getByRole("button", { name: "Xóa tài liệu" }));
    await waitFor(() => expect(screen.queryByText("baogia.pdf")).not.toBeInTheDocument());
    expect(api.deleteDocument).toHaveBeenCalledWith("d1");
    expect(tracker.events.map((e) => e.name)).toContain("document_deleted");
  });

  it("xóa lỗi: giữ hộp thoại để thử lại và báo lỗi", async () => {
    const api = ready({
      deleteDocument: vi.fn(async () => {
        throw new Error("x");
      }),
    });
    renderApp(<Workspace />, { api });
    const user = userEvent.setup();
    await user.click(await screen.findByRole("button", { name: "Xóa baogia.pdf" }));
    const dlg = screen.getByRole("dialog", { name: "Xóa tài liệu?" });
    await user.click(within(dlg).getByRole("button", { name: "Xóa tài liệu" }));
    expect(await screen.findByText(/Chưa xóa được/)).toBeInTheDocument();
    expect(dlg).toHaveAttribute("open");
  });

  it("phát hiện tài liệu chuyển processing → ready khi làm mới và thông báo", async () => {
    let state: "processing" | "ready" = "processing";
    const api = fakeApi({
      listDocuments: vi.fn(async () => [
        doc({ status: state, pageCount: state === "ready" ? 3 : null }),
      ]),
    });
    const { tracker } = renderApp(<Workspace />, { api });
    expect(await screen.findByText("Đang xử lý")).toBeInTheDocument();
    state = "ready";
    window.dispatchEvent(new Event("focus")); // quay lại tab ⇒ làm mới ngay
    expect(await screen.findByText("Sẵn sàng")).toBeInTheDocument();
    expect(tracker.events.map((e) => e.name)).toContain("document_ready");
    expect(await screen.findByText("“baogia.pdf” đã sẵn sàng.")).toBeInTheDocument();
  });
});

describe("Workspace — trợ năng (axe, không tính tương phản màu vì jsdom không có CSS)", () => {
  it("không có vi phạm WCAG 2 A/AA ở màn chính có hội thoại", async () => {
    const { container } = renderApp(<Workspace />, { api: ready() });
    await ask("q");
    const msg = await screen.findByTestId("ai-message");
    await waitFor(() => expect(msg).toHaveAttribute("data-status", "complete"));
    const res = await axe.run(container, {
      runOnly: ["wcag2a", "wcag2aa"],
      rules: { "color-contrast": { enabled: false }, region: { enabled: false } },
    });
    expect(res.violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(" | ")}`)).toEqual(
      [],
    );
  });
});
