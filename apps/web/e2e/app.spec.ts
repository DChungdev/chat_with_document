import { expect, test } from "@playwright/test";
import { acceptNotice, ask, fixture, login, upload, waitReady } from "./helpers";

test.describe("Luồng chính của Lan (US-101…103, 201…203, 301, 302, 401)", () => {
  test("cổng thông báo dữ liệu chặn tải lên cho tới khi xác nhận", async ({ page }) => {
    await login(page);
    const dlg = page.getByRole("dialog", { name: /Chào mừng/ });
    await expect(dlg).toBeVisible();
    // Chưa xác nhận: nút Tiếp tục tắt, Esc không đóng được, tải lên bị khóa phía sau
    await expect(dlg.getByRole("button", { name: "Tiếp tục" })).toBeDisabled();
    await page.keyboard.press("Escape");
    await expect(dlg).toBeVisible();
    await dlg.getByRole("checkbox").check();
    await expect(dlg.getByRole("button", { name: "Tiếp tục" })).toBeEnabled();
    await dlg.getByRole("button", { name: "Tiếp tục" }).click();
    await expect(dlg).toBeHidden();
    await expect(page.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled();
    // Xem lại thông báo bất cứ lúc nào, ở chế độ chỉ đọc
    await page.getByRole("button", { name: "Thông báo dữ liệu" }).click();
    await expect(dlg.getByRole("checkbox")).toBeChecked();
    await expect(dlg.getByRole("checkbox")).toBeDisabled();
    await dlg.getByRole("button", { name: "Đóng" }).click();
    await expect(dlg).toBeHidden();
  });

  test("tải PDF → Sẵn sàng → hỏi → trả lời có trích dẫn đúng trang → xem nguồn", async ({
    page,
  }) => {
    await login(page);
    await acceptNotice(page);
    await expect(page.getByText("Hãy tải PDF để bắt đầu")).toBeVisible();
    await expect(page.getByLabel("Câu hỏi của bạn")).toBeDisabled();

    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    await expect(page.getByLabel("Câu hỏi của bạn")).toBeEnabled();

    await ask(page, "Thanh toán trong vòng bao nhiêu ngày kể từ ngày nhận hóa đơn?");
    // đang stream: có con trỏ, nút Gửi chuyển thành Dừng
    await expect(page.getByRole("button", { name: "Dừng tạo câu trả lời" })).toBeVisible();
    const answer = page.getByTestId("ai-message").last();
    await expect(answer).toHaveAttribute("data-status", "complete", { timeout: 20_000 });
    await expect(answer).toContainText("30 ngày");
    await expect(answer).not.toContainText("[S"); // nhãn nguồn đã bị bóc khỏi văn bản
    await expect(answer.getByText("Do AI tạo")).toBeVisible();

    const chip = answer.getByRole("button", { name: /baogia\.pdf · tr\.2/ });
    await expect(chip).toBeVisible();
    await chip.click();
    const panel = page.getByRole("complementary", { name: "Nguồn dẫn" });
    await expect(panel).toContainText("baogia.pdf");
    await expect(panel).toContainText("Trang 2");
    await expect(panel.locator("blockquote")).toContainText("Thanh toán trong vòng 30 ngày");
    // Esc đóng panel và trả focus về chip (WCAG 2.4.3)
    await page.keyboard.press("Escape");
    await expect(chip).toBeFocused();
    await expect(chip).toHaveAttribute("aria-expanded", "false");
  });

  test("câu hỏi ngoài phạm vi: báo không tìm thấy, không có trích dẫn", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    await ask(page, "Thời tiết Hà Nội hôm nay thế nào?");
    const answer = page.getByTestId("ai-message").last();
    await expect(answer).toHaveAttribute("data-status", "complete", { timeout: 20_000 });
    await expect(answer).toContainText("Không tìm thấy thông tin này");
    await expect(answer.locator(".chip")).toHaveCount(0);
    await expect(answer.locator(".bubble")).toHaveClass(/not-grounded/);
  });

  test("tài liệu lỗi hiển thị lý do riêng và không ảnh hưởng tài liệu khác", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "scan.pdf", "matkhau.pdf", "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    await expect(page.locator(".doc-item", { hasText: "scan.pdf" })).toContainText("PDF quét");
    await expect(page.locator(".doc-item", { hasText: "matkhau.pdf" })).toContainText(
      "PDF có mật khẩu",
    );
    // tài liệu lỗi không chọn được để hỏi
    await expect(
      page.locator(".doc-item", { hasText: "scan.pdf" }).getByRole("checkbox"),
    ).toBeDisabled();
  });

  test("tệp giả PDF bị server từ chối với thông báo rõ ràng và có thể bỏ qua", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "khong-phai-pdf.pdf");
    const item = page.locator(".doc-item", { hasText: "khong-phai-pdf.pdf" });
    await expect(item).toContainText("Tải thất bại");
    await expect(page.locator(".toast")).toContainText("không phải PDF hợp lệ");
    await item.getByRole("button", { name: "Bỏ qua" }).click();
    await expect(item).toHaveCount(0);
  });

  test("xóa tài liệu: hộp xác nhận, rồi nguồn dẫn cũ báo không còn khả dụng", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    await ask(page, "Thiết bị camera được bảo hành bao lâu kể từ ngày nghiệm thu?");
    const answer = page.getByTestId("ai-message").last();
    await expect(answer).toHaveAttribute("data-status", "complete", { timeout: 20_000 });

    await page.getByRole("button", { name: "Xóa baogia.pdf" }).click();
    const dlg = page.getByRole("dialog", { name: "Xóa tài liệu?" });
    await expect(dlg).toBeVisible();
    await dlg.getByRole("button", { name: "Hủy" }).click(); // hủy không xóa gì
    await expect(page.locator(".doc-item", { hasText: "baogia.pdf" })).toHaveCount(1);

    await page.getByRole("button", { name: "Xóa baogia.pdf" }).click();
    await dlg.getByRole("button", { name: "Xóa tài liệu" }).click();
    await expect(page.locator(".doc-item")).toHaveCount(0);
    await expect(page.locator(".toast", { hasText: "Đã xóa" })).toBeVisible();

    const chip = answer.locator(".chip").first();
    await expect(chip).toHaveClass(/invalid/);
    await chip.click();
    await expect(page.getByRole("complementary", { name: "Nguồn dẫn" })).toContainText(
      "Nguồn không còn khả dụng",
    );
  });
});

test.describe("Dừng, gián đoạn và khôi phục (US-205)", () => {
  test("bấm Dừng giữ lại phần đã nhận, rồi Hỏi lại tạo câu trả lời mới", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    await ask(page, "Thanh toán trong vòng bao nhiêu ngày kể từ ngày nhận hóa đơn?");
    const answer = page.getByTestId("ai-message").last();
    await expect(answer).toHaveAttribute("data-status", "streaming");
    await page.getByRole("button", { name: "Dừng tạo câu trả lời" }).click();
    await expect(answer).toHaveAttribute("data-status", "stopped", { timeout: 10_000 });
    await expect(answer).toContainText("Đã dừng");
    await expect(page.getByTestId("ai-message")).toHaveCount(1);
    await answer.getByRole("button", { name: "Hỏi lại" }).click();
    await expect(answer).toHaveAttribute("data-status", "complete", { timeout: 20_000 });
    await expect(answer).toContainText("30 ngày");
  });

  test("mất kết nối giữa chừng: giữ câu hỏi, nút Thử lại hoạt động", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    // Chặn lần hỏi đầu để mô phỏng đứt mạng; lần sau cho đi qua
    let blocked = true;
    await page.route("**/api/v1/conversations/*/messages", async (route) => {
      if (blocked) return route.abort("connectionreset");
      return route.continue();
    });
    await ask(page, "Thanh toán trong vòng bao nhiêu ngày kể từ ngày nhận hóa đơn?");
    const answer = page.getByTestId("ai-message").last();
    await expect(answer).toHaveAttribute("data-status", "failed");
    await expect(answer).toContainText("Câu hỏi của bạn vẫn được giữ");
    await expect(page.locator(".msg-user")).toHaveCount(1);
    blocked = false;
    await answer.getByRole("button", { name: "Thử lại" }).click();
    await expect(answer).toHaveAttribute("data-status", "complete", { timeout: 20_000 });
    await expect(page.locator(".msg-user")).toHaveCount(1); // không nhân đôi câu hỏi
  });
});

test.describe("Hết phiên (SCR-07) và kill switch (SCR-08)", () => {
  test("hết phiên: hiện overlay, giữ bản nháp, đăng nhập lại là tiếp tục được", async ({
    page,
  }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    const box = page.getByLabel("Câu hỏi của bạn");
    await box.fill("Thiết bị được bảo hành bao lâu?");

    await page.route("**/api/v1/documents*", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/problem+json",
        body: JSON.stringify({
          title: "Chưa xác thực",
          status: 401,
          code: "SESSION_EXPIRED",
          detail: "hết hạn",
        }),
      }),
    );
    const dlg = page.getByRole("dialog", { name: "Phiên làm việc đã hết hạn" });
    await page.evaluate(() => window.dispatchEvent(new Event("focus"))); // quay lại tab ⇒ làm mới ngay
    await expect(dlg).toBeVisible({ timeout: 15_000 }); // lần polling tài liệu kế tiếp nhận 401
    await page.keyboard.press("Escape");
    await expect(dlg).toBeVisible(); // không đóng được bằng Esc
    await page.unroute("**/api/v1/documents*");
    await dlg.getByRole("button", { name: "Đăng nhập lại" }).click();
    await expect(dlg).toBeHidden();
    await expect(box).toHaveValue("Thiết bị được bảo hành bao lâu?"); // bản nháp còn nguyên
  });

  test("kill switch: banner hiện khi hỏi đáp bị tắt và biến mất khi bật lại", async ({
    page,
    request,
  }) => {
    const name = await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");

    const opsToken = (
      await (
        await request.post("/api/v1/dev/login", {
          data: { name: `ops-${name}`, roles: ["user", "ops"] },
        })
      ).json()
    ).accessToken;
    const flag = (enabled: boolean) =>
      request.put("/api/v1/admin/flags/qa-enabled", {
        data: { enabled },
        headers: { Authorization: `Bearer ${opsToken}` },
      });
    expect((await flag(false)).status()).toBe(204);
    try {
      await ask(page, "Thiết bị camera được bảo hành bao lâu?");
      await expect(page.locator(".global-banner")).toContainText(
        "Hỏi đáp tạm thời không khả dụng",
        {
          timeout: 15_000,
        },
      );
      await expect(page.getByLabel("Câu hỏi của bạn")).toBeDisabled();
      await expect(page.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled(); // tài liệu vẫn dùng được
    } finally {
      expect((await flag(true)).status()).toBe(204);
    }
  });
});

test.describe("Báo cáo đánh giá MVP (SCR-09, US-501)", () => {
  test("người đánh giá thấy báo cáo; ghi rõ chưa thể kết luận khi chưa duyệt mục tiêu", async ({
    page,
  }) => {
    await login(page, undefined, "evaluator");
    await acceptNotice(page);
    await page.getByRole("link", { name: "Báo cáo" }).click();
    await expect(page.getByRole("heading", { name: /Báo cáo đánh giá MVP/ })).toBeVisible();
    await expect(page.getByText("Chưa thể kết luận").first()).toBeVisible();
    for (const id of ["MET-001", "MET-002", "KR1.2", "KR2.2"]) {
      await expect(page.getByTestId(`metric-${id}`)).toBeVisible();
    }
    await expect(page.getByText("Quyền riêng tư")).toBeVisible();
  });

  test("người dùng thường không có liên kết báo cáo và bị từ chối nếu vào thẳng", async ({
    page,
  }) => {
    await login(page);
    await acceptNotice(page);
    await expect(page.getByRole("link", { name: "Báo cáo" })).toHaveCount(0);
    await page.goto("/#/report");
    await expect(page.getByText("Bạn không có quyền xem báo cáo này")).toBeVisible();
  });

  test("telemetry của phiên làm việc đi vào báo cáo (không có nội dung)", async ({ browser }) => {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    await ask(page, "Thiết bị camera được bảo hành bao lâu kể từ ngày nghiệm thu?");
    await expect(page.getByTestId("ai-message").last()).toHaveAttribute("data-status", "complete", {
      timeout: 20_000,
    });
    await page.goto("/#/?trial=1");
    await page.reload();
    await page.getByRole("button", { name: "Tôi đã có thông tin cần tìm" }).click();
    await page.waitForTimeout(500);
    await page.evaluate(() => document.dispatchEvent(new Event("visibilitychange"))); // flush qua beforeunload
    await ctx.close();

    const ev = await browser.newContext();
    const p2 = await ev.newPage();
    await login(p2, undefined, "evaluator");
    await p2.goto("/#/report");
    await expect(p2.getByTestId("metric-KR2.2")).toBeVisible();
    // Dữ liệu từ phiên trước phải hiện ở phễu (ít nhất một phiên đã bắt đầu)
    await expect(async () => {
      await p2.reload();
      const cell = p2.locator("tr", { hasText: "session_started" }).locator("td").nth(1);
      expect(Number(await cell.textContent())).toBeGreaterThanOrEqual(1);
    }).toPass({ timeout: 20_000 });
    await ev.close();
  });
});

test.describe("Bố cục đáp ứng", () => {
  test("dưới 1024px danh sách tài liệu thành ngăn kéo mở bằng nút menu", async ({ page }) => {
    await page.setViewportSize({ width: 800, height: 900 });
    await login(page);
    await acceptNotice(page);
    const menu = page.getByRole("button", { name: "Mở danh sách tài liệu" });
    await expect(menu).toBeVisible();
    const panel = page.locator("#panel-docs");
    await expect(panel).not.toHaveClass(/open/);
    await menu.click();
    await expect(panel).toHaveClass(/open/);
    await expect(page.getByRole("button", { name: "Tải PDF lên" })).toBeVisible();
  });
});

test("fixture PDF tồn tại", () => {
  expect(fixture("baogia.pdf")).toContain("baogia.pdf");
});
