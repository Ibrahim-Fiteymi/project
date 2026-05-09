/**
 * AuthContext — single source of truth for the authenticated user on the
 * frontend. Token persistence lives in `auth.ts`; this module wraps it in a
 * React context so components can call `useAuth()` and trigger re-renders
 * when login/logout happens.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  apiLogin,
  apiLogout,
  apiRegister,
  refreshIfPossible,
  tokens,
  type AuthUser,
} from "./auth";

interface AuthContextShape {
  user: AuthUser | null;
  isAuthenticated: boolean;
  initialising: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextShape | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => tokens.user());
  const [initialising, setInitialising] = useState(true);

  // On mount, if we have a refresh token but no valid access token, attempt a
  // silent refresh so a tab reload doesn't kick the user back to /login.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const access = tokens.access();
      const refresh = tokens.refresh();
      if (!access && refresh) {
        const pair = await refreshIfPossible();
        if (!cancelled && pair) setUser(pair.user);
      }
      if (!cancelled) setInitialising(false);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const pair = await apiLogin(email, password);
    tokens.save(pair);
    setUser(pair.user);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const pair = await apiRegister(email, password);
    tokens.save(pair);
    setUser(pair.user);
  }, []);

  const logout = useCallback(async () => {
    const access = tokens.access();
    const refresh = tokens.refresh();
    if (access) await apiLogout(access, refresh);
    tokens.clear();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextShape>(
    () => ({
      user,
      isAuthenticated: user !== null,
      initialising,
      login,
      register,
      logout,
    }),
    [user, initialising, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextShape {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
