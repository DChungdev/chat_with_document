import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { acceptNotice, ask, login, upload, waitReady } from "./helpers";

// E12: WCAG 2.1 AA trong trình duyệt thật (có cả kiểm tra tương phản màu mà jsdom không làm được).
async function audit(page: Page, label: string) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  const bad = results.violations.map(
    (v) => `${v.id} (${v.impact}): ${v.nodes.map((n) => n.target.join(" ")).join(" | ")}`,
  );
  expect(bad, `${label}\n${bad.join("\n")}`).toEqual([]);
}

test.describe("Trợ năng (WCAG 2.1 AA)", () => {
  test("màn đăng nhập", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Đăng nhập" })).toBeVisible();
    await audit(page, "login");
  });

  test("cổng thông báo dữ liệu", async ({ page }) => {
    await login(page);
    await expect(page.getByRole("dialog", { name: /Chào mừng/ })).toBeVisible();
    await audit(page, "notice");
  });

  test("màn chính trống, đang xử lý và có hội thoại + nguồn dẫn", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await audit(page, "empty");

    await upload(page, "baogia.pdf", "scan.pdf");
    await expect(page.locator(".doc-item", { hasText: "scan.pdf" })).toContainText("PDF quét", {
      timeout: 20_000,
    });
    await waitReady(page, "baogia.pdf");
    await audit(page, "documents");

    await ask(page, "Thanh toán trong vòng bao nhiêu ngày kể từ ngày nhận hóa đơn?");
    const answer = page.getByTestId("ai-message").last();
    await expect(answer).toHaveAttribute("data-status", "complete", { timeout: 20_000 });
    await audit(page, "chat");

    await answer.locator(".chip").first().click();
    await expect(page.getByRole("complementary", { name: "Nguồn dẫn" })).toContainText("Trang 2");
    await audit(page, "source panel");
  });

  test("hộp thoại xóa và báo cáo", async ({ page }) => {
    await login(page, undefined, "evaluator");
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    await page.getByRole("button", { name: "Xóa baogia.pdf" }).click();
    await expect(page.getByRole("dialog", { name: "Xóa tài liệu?" })).toBeVisible();
    await audit(page, "delete dialog");
    await page.getByRole("button", { name: "Hủy" }).click();
    await page.getByRole("link", { name: "Báo cáo" }).click();
    await expect(page.getByRole("heading", { name: /Báo cáo đánh giá MVP/ })).toBeVisible();
    await audit(page, "report");
  });

  test("dùng được hoàn toàn bằng bàn phím: gửi câu hỏi và mở nguồn dẫn", async ({ page }) => {
    await login(page);
    await acceptNotice(page);
    await upload(page, "baogia.pdf");
    await waitReady(page, "baogia.pdf");
    // Liên kết "Bỏ qua" đưa focus thẳng tới ô nhập
    await page.keyboard.press("Tab");
    await page.getByRole("link", { name: "Bỏ qua tới ô nhập câu hỏi" }).press("Enter");
    await page.getByLabel("Câu hỏi của bạn").focus();
    await page.keyboard.type("Thiết bị camera được bảo hành bao lâu kể từ ngày nghiệm thu?");
    await page.keyboard.press("Enter");
    const answer = page.getByTestId("ai-message").last();
    await expect(answer).toHaveAttribute("data-status", "complete", { timeout: 20_000 });
    const chip = answer.locator(".chip").first();
    await chip.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("complementary", { name: "Nguồn dẫn" })).toContainText("Trang 3");
    await page.keyboard.press("Escape");
    await expect(chip).toBeFocused();
  });

  test("tôn trọng prefers-reduced-motion", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await login(page);
    const dur = await page.evaluate(
      () => getComputedStyle(document.querySelector(".btn")!).transitionDuration,
    );
    expect(parseFloat(dur)).toBeLessThan(0.01);
  });
});
