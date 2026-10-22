// Bộ biểu tượng theo prototype (docs/design/UI_UX_design/app.html). Trang trí: luôn kèm chữ ở nơi có nghĩa.
const PATHS = {
  menu: "M3 6h18M3 12h18M3 18h18",
  info: "M12 11v5M12 8h.01",
  upload: "M12 16V4M7 9l5-5 5 5M4 20h16",
  file: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z M14 3v5h5",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3",
  send: "M22 2 11 13M22 2l-7 20-4-9-9-4z",
  copy: "M5 15V5a2 2 0 0 1 2-2h8",
  up: "M7 11v9H4v-9zM7 11l4-8a2 2 0 0 1 2 2v4h6a2 2 0 0 1 2 2l-1 6a2 2 0 0 1-2 2H7",
  down: "M17 13V4h3v9zM17 13l-4 8a2 2 0 0 1-2-2v-4H5a2 2 0 0 1-2-2l1-6a2 2 0 0 1 2-2h11",
  x: "M6 6l12 12M18 6 6 18",
  check: "M5 12l5 5L20 7",
  alert: "M12 3 2 21h20zM12 10v5M12 18h.01",
  clock: "M12 7v5l3 2",
  refresh: "M21 12a9 9 0 1 1-3-6.7M21 4v5h-5",
  arrowDown: "M12 5v14M6 13l6 6 6-6",
  sparkle: "M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2z",
  lock: "M8 11V7a4 4 0 0 1 8 0v4",
} as const;

export type IconName = keyof typeof PATHS | "stop";

export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      {name === "stop" && <rect x="6" y="6" width="12" height="12" rx="2" />}
      {(name === "info" || name === "clock") && <circle cx="12" cy="12" r="9" />}
      {name === "copy" && <rect x="9" y="9" width="12" height="12" rx="2" />}
      {name === "lock" && <rect x="5" y="11" width="14" height="10" rx="2" />}
      {name !== "stop" && <path d={PATHS[name]} />}
    </svg>
  );
}
