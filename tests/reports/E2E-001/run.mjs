import { startCase } from "../../tools/tc.mjs";

const tc = await startCase("E2E-001", { title: "Hành trình chính của Lan" });
const { page, expect } = tc;

await tc.step("Đăng nhập dev bằng tài khoản mới", "Vào được trang chính, thấy hộp thoại thông báo dữ liệu", async () => {
  await tc.login();
  await expect(page.getByRole("dialog", { name: /Chào mừng/ })).toBeVisible();
});
await tc.step("Xác nhận thông báo dữ liệu", "Hộp thoại đóng, nút Tải PDF lên khả dụng", async () => {
  await tc.acceptNotice();
  await expect(page.getByRole("button", { name: "Tải PDF lên" })).toBeEnabled();
});
await tc.step("Tải baogia.pdf", "Tệp xuất hiện trong danh sách rồi chuyển Sẵn sàng", async () => {
  await tc.upload("baogia.pdf");
  await tc.waitReady("baogia.pdf");
});
await tc.step("Hỏi về điều khoản thanh toán", "Trả lời streaming, chứa '30 ngày', có chip baogia.pdf · tr.2", async () => {
  await tc.ask("Thanh toán trong vòng bao nhiêu ngày kể từ ngày nhận hóa đơn?");
  const a = await tc.waitAnswer();
  await expect(a).toContainText("30 ngày");
  await expect(a.getByRole("button", { name: /baogia\.pdf · tr\.2/ })).toBeVisible();
});
await tc.step("Mở panel nguồn dẫn", "Panel hiện đúng tệp, Trang 2 và đoạn gốc", async () => {
  const a = page.getByTestId("ai-message").last();
  await a.getByRole("button", { name: /baogia\.pdf · tr\.2/ }).click();
  const panel = page.getByRole("complementary", { name: "Nguồn dẫn" });
  await expect(panel).toContainText("Trang 2");
  await expect(panel.locator("blockquote")).toContainText("Thanh toán trong vòng 30 ngày");
});
await tc.step("Xóa baogia.pdf", "Danh sách trống; chip cũ báo 'Nguồn không còn khả dụng'", async () => {
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Xóa baogia.pdf" }).click();
  await page.getByRole("dialog", { name: "Xóa tài liệu?" }).getByRole("button", { name: "Xóa tài liệu" }).click();
  await expect(page.locator(".doc-item")).toHaveCount(0);
  await page.getByTestId("ai-message").last().locator(".chip").first().click();
  await expect(page.getByRole("complementary", { name: "Nguồn dẫn" })).toContainText("Nguồn không còn khả dụng");
});
await tc.finish();
