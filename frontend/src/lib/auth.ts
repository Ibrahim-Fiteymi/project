/**
 * Token storage + auth API client.
 *
 * Tokens live in localStorage so they survive a tab refresh. The XSS exposure
 * of localStorage is acknowledged in SECURITY.md; the alternative — httpOnly
 * cookies — would require credentialed CORS and CSRF tokens, which are out of
 * scope for the course-deliverable MVP.
 */

import { API_BASE } from "../api";

const ACCESS_KEY = "nuclei.access.v1";
const REFRESH_KEY = "nuclei.refresh.v1";
const USER_KEY = "nuclei.user.v1";

export interface AuthUser {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

function safeGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key: string, value: string | null): void {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    /* ignore quota / privacy mode errors */
  }
}

export const tokens = {
  access: () => safeGet(ACCESS_KEY),
  refresh: () => safeGet(REFRESH_KEY),
  user: (): AuthUser | null => {
    const raw = safeGet(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  },
  save: (pair: TokenPair) => {
    safeSet(ACCESS_KEY, pair.access_token);
    safeSet(REFRESH_KEY, pair.refresh_token);
    safeSet(USER_KEY, JSON.stringify(pair.user));
  },
  clear: () => {
    safeSet(ACCESS_KEY, null);
    safeSet(REFRESH_KEY, null);
    safeSet(USER_KEY, null);
  },
};

async function parseDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    /* ignore */
  }
  return fallback;
}

export async function apiLogin(email: string, password: string): Promise<TokenPair> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseDetail(res, `Login failed (${res.status})`));
  return res.json();
}

export async function apiRegister(email: string, password: string): Promise<TokenPair> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseDetail(res, `Registration failed (${res.status})`));
  return res.json();
}

export async function apiRefresh(refreshToken: string): Promise<TokenPair> {
  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) throw new Error(await parseDetail(res, `Refresh failed (${res.status})`));
  return res.json();
}

export async function apiLogout(accessToken: string, refreshToken: string | null): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken ?? undefined }),
    });
  } catch {
    /* logout is best-effort: clearing local tokens is what really matters */
  }
}

/**
 * Centralised refresh handshake used by api.ts. Coalesces concurrent
 * 401-driven refresh attempts so the second tab/request doesn't burn a
 * second refresh token rotation.
 */
let inflightRefresh: Promise<TokenPair | null> | null = null;

export async function refreshIfPossible(): Promise<TokenPair | null> {
  if (inflightRefresh) return inflightRefresh;
  const refreshToken = tokens.refresh();
  if (!refreshToken) return null;
  inflightRefresh = (async () => {
    try {
      const pair = await apiRefresh(refreshToken);
      tokens.save(pair);
      return pair;
    } catch {
      tokens.clear();
      return null;
    } finally {
      inflightRefresh = null;
    }
  })();
  return inflightRefresh;
}
