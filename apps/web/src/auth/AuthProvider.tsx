import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { HttpClient } from "../api/client";
import { createApi, type Api } from "../api/api";

/**
 * Cơ chế đăng nhập thật chưa chốt [TBD: OQ-014]. Hiện chỉ có đăng nhập DEV (server chỉ bật ở môi trường
 * dev). Phần còn lại của UI chỉ phụ thuộc vào `token`, `roles`, `markExpired` nên thay bằng OIDC sau này
 * không đụng tới các màn hình.
 */
const STORAGE_KEY = "docchat.session";

interface Session {
  token: string;
  subject: string;
  roles: string[];
  name: string;
}

function readSession(): Session | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null; // sessionStorage bị chặn (chế độ riêng tư): chạy không lưu
  }
}
function writeSession(s: Session | null): void {
  try {
    if (s) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s));
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* bỏ qua */
  }
}

interface AuthValue {
  session: Session | null;
  /** true khi server trả 401: hiện overlay đăng nhập lại, giữ nguyên màn hình bên dưới (SCR-07). */
  expired: boolean;
  api: Api;
  login(name: string, roles: string[]): Promise<void>;
  logout(): void;
}

const Ctx = createContext<AuthValue | null>(null);

export function useAuth(): AuthValue {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth cần AuthProvider");
  return v;
}

/** Cho test: cung cấp sẵn Api giả và phiên. */
export function AuthTestProvider({
  api,
  session,
  expired = false,
  children,
}: {
  api: Api;
  session: Session | null;
  expired?: boolean;
  children: ReactNode;
}) {
  const value = useMemo<AuthValue>(
    () => ({ session, expired, api, login: async () => undefined, logout: () => undefined }),
    [api, session, expired],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export type { Session };

export function AuthProvider({
  children,
  fetchImpl,
}: {
  children: ReactNode;
  fetchImpl?: typeof fetch;
}) {
  const [session, setSession] = useState<Session | null>(readSession);
  const [expired, setExpired] = useState(false);
  const tokenRef = useRef<string | null>(session?.token ?? null);

  const api = useMemo(() => {
    const http = new HttpClient({
      getToken: () => tokenRef.current,
      onUnauthorized: () => {
        if (tokenRef.current) setExpired(true); // chưa đăng nhập thì 401 là bình thường
      },
      fetchImpl,
    });
    return createApi(http);
  }, [fetchImpl]);

  const login = useCallback(
    async (name: string, roles: string[]) => {
      const res = await api.devLogin(name, roles);
      const next: Session = {
        token: res.accessToken,
        subject: res.subject,
        roles: res.roles,
        name,
      };
      tokenRef.current = next.token;
      writeSession(next);
      setSession(next);
      setExpired(false);
    },
    [api],
  );

  const logout = useCallback(() => {
    tokenRef.current = null;
    writeSession(null);
    setSession(null);
    setExpired(false);
  }, []);

  const value = useMemo(
    () => ({ session, expired, api, login, logout }),
    [session, expired, api, login, logout],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
