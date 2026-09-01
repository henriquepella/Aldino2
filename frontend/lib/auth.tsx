"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, getToken, setToken } from "./api";
import type { UserOut } from "./types";

interface AuthState {
  user: UserOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  loginDemo: () => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthState | null>(null);

const DEMO = { email: "demo@demo.local", password: "demo12345" };

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const finish = useCallback(async () => {
    const u = await api.me();
    setUser(u);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const t = await api.login(email, password);
      setToken(t.access_token);
      await finish();
    },
    [finish],
  );

  const register = useCallback(
    async (email: string, password: string, name: string) => {
      const t = await api.register(email, password, name);
      setToken(t.access_token);
      await finish();
    },
    [finish],
  );

  const loginDemo = useCallback(async () => {
    try {
      await login(DEMO.email, DEMO.password);
    } catch {
      await register(DEMO.email, DEMO.password, "Demonstração").catch(() =>
        login(DEMO.email, DEMO.password),
      );
    }
  }, [login, register]);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    router.push("/login");
  }, [router]);

  return (
    <Ctx.Provider value={{ user, loading, login, register, loginDemo, logout }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth fora de AuthProvider");
  return c;
}
