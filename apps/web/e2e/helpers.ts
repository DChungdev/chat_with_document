import { expect, type Page } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const fixture = (name: string): string => path.join(here, "fixtures", name);

let counter = 0;
/** Tên người dùng duy nhất cho mỗi test ⇒ dữ liệu cô lập dù dùng chung một máy chủ. */
export const uniqueUser = (prefix = "lan"): string =>
  `${prefix}${Date.now().toString(36)}${counter++}`;

export async function login(page: Page, name = uniqueUser(), role = "user"): Promise<string> {
  await page.goto("/");
  await page.getByLabel("Tên của bạn").fill(name);
  if (role !== "user") await page.getByLabel("Vai trò").selectOption(role);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByRole("heading", { name: "Chat với tài liệu", level: 1 })).toBeVisible();
  return name;
}

export async function acceptNotice(page: Page): Promise<void> {
  const dlg = page.getByRole("dialog", { name: /Chào mừng/ });
  await expect(dlg).toBeVisible();
  await dlg.getByRole("checkbox").check();
  await dlg.getByRole("button", { name: "Tiếp tục" }).click();
  await expect(dlg).toBeHidden();
}

export async function upload(page: Page, ...files: string[]): Promise<void> {
  await page.getByTestId("file-input").setInputFiles(files.map(fixture));
}

export async function waitReady(page: Page, name: string): Promise<void> {
  const item = page.locator(".doc-item", { hasText: name });
  await expect(item.getByText("Sẵn sàng")).toBeVisible({ timeout: 20_000 });
}

export async function ask(page: Page, question: string): Promise<void> {
  const box = page.getByLabel("Câu hỏi của bạn");
  await box.fill(question);
  await box.press("Enter");
}
