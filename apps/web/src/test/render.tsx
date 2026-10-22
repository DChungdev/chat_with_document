import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import type { Api } from "../api/api";
import { AuthTestProvider, type Session } from "../auth/AuthProvider";
import { TelemetryTestProvider } from "../telemetry/TelemetryProvider";
import type { Tracker } from "../telemetry/telemetry";
import { ToastProvider } from "../ui/Toasts";

export const SESSION: Session = { token: "t", subject: "dev|lan", roles: ["user"], name: "Lan" };

export function spyTracker(): Tracker & {
  events: { name: string; props: Record<string, unknown> }[];
} {
  const events: { name: string; props: Record<string, unknown> }[] = [];
  return {
    events,
    track: (name, props = {}) => void events.push({ name, props }),
    flush: async () => undefined,
    dispose: () => undefined,
  };
}

/** Bọc component trong các provider thật (toast, auth, telemetry) với Api/Tracker giả. */
export function renderApp(
  ui: ReactElement,
  opts: { api: Api; tracker?: Tracker; session?: Session | null; expired?: boolean },
) {
  const tracker = opts.tracker ?? spyTracker();
  const result = render(
    <ToastProvider>
      <AuthTestProvider
        api={opts.api}
        session={opts.session === undefined ? SESSION : opts.session}
        expired={opts.expired}
      >
        <TelemetryTestProvider tracker={tracker}>{ui}</TelemetryTestProvider>
      </AuthTestProvider>
    </ToastProvider>,
  );
  return { ...result, tracker: tracker as ReturnType<typeof spyTracker> };
}
