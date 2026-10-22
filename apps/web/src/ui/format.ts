export function fmtSize(bytes: number): string {
  return bytes >= 1_048_576
    ? `${(bytes / 1_048_576).toFixed(1)} MB`
    : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function fmtAge(iso: string | number, now: number = Date.now()): string {
  const t = typeof iso === "number" ? iso : Date.parse(iso);
  const minutes = Math.floor((now - t) / 60_000);
  if (minutes < 1) return "vừa xong";
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours} giờ trước` : `${Math.floor(hours / 24)} ngày trước`;
}

/** UUID v4; `crypto.randomUUID` chỉ có ở ngữ cảnh an toàn (https/localhost) nên cần dự phòng. */
export function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}
