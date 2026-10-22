import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import { LoginScreen } from "./auth/LoginScreen";
import { SessionExpiredDialog } from "./auth/SessionExpiredDialog";
import { ReportPage } from "./features/report/ReportPage";
import { Workspace } from "./features/workspace/Workspace";
import { TelemetryProvider } from "./telemetry/TelemetryProvider";
import { ToastProvider } from "./ui/Toasts";

/** Định tuyến băm: "#/" ứng dụng, "#/report" báo cáo (SCR-09); "?trial=1" bật thanh ghi nhận tác vụ (OQ-005). */
export function parseHash(hash: string): { route: "app" | "report"; trial: boolean } {
  const [path, query = ""] = hash.replace(/^#/, "").split("?");
  return {
    route: path === "/report" ? "report" : "app",
    trial: new URLSearchParams(query).get("trial") === "1",
  };
}

function useHash(): string {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const on = () => setHash(window.location.hash);
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return hash;
}

function Shell() {
  const { session } = useAuth();
  const { route, trial } = parseHash(useHash());
  if (!session) return <LoginScreen />;
  return (
    <TelemetryProvider>
      {route === "report" ? <ReportPage /> : <Workspace trial={trial} />}
      <SessionExpiredDialog />
    </TelemetryProvider>
  );
}

export function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </ToastProvider>
  );
}
