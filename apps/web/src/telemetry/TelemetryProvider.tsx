import { createContext, useContext, useEffect, useMemo, type ReactNode } from "react";
import { useAuth } from "../auth/AuthProvider";
import { TelemetryClient, type Tracker } from "./telemetry";

const noop: Tracker = {
  track: () => undefined,
  flush: async () => undefined,
  dispose: () => undefined,
};
const Ctx = createContext<Tracker>(noop);
export const useTelemetry = (): Tracker => useContext(Ctx);

/** Cho test: truyền Tracker giả để kiểm tra sự kiện được phát. */
export function TelemetryTestProvider({
  tracker,
  children,
}: {
  tracker: Tracker;
  children: ReactNode;
}) {
  return <Ctx.Provider value={tracker}>{children}</Ctx.Provider>;
}

export function TelemetryProvider({ children }: { children: ReactNode }) {
  const { api, session } = useAuth();
  const client = useMemo(
    () =>
      session
        ? new TelemetryClient({ send: (events, keepalive) => api.sendTelemetry(events, keepalive) })
        : null,
    // phiên mới (đăng nhập lại người khác) ⇒ client mới, sessionId mới
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [api, session?.subject],
  );

  useEffect(() => {
    if (!client) return;
    client.track("session_started", { entry_source: "direct" });
    const onHide = () => {
      if (document.visibilityState === "hidden") void client.flush(true);
    };
    document.addEventListener("visibilitychange", onHide);
    return () => {
      document.removeEventListener("visibilitychange", onHide);
      void client.flush(true);
      client.dispose();
    };
  }, [client]);

  return <Ctx.Provider value={client ?? noop}>{children}</Ctx.Provider>;
}
