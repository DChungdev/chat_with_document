import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
  try {
    sessionStorage.clear();
  } catch {
    /* bỏ qua */
  }
});

// jsdom chưa cài <dialog>.showModal()/close(): mô phỏng đủ để kiểm tra hành vi mở/đóng.
if (typeof HTMLDialogElement !== "undefined") {
  HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
}

Element.prototype.scrollIntoView ||= () => undefined;
