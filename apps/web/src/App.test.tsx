import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { App } from "./App";

test("hiển thị tiêu đề ứng dụng", () => {
  render(<App />);
  expect(screen.getByRole("heading", { name: "Chat với tài liệu" })).toBeTruthy();
});
