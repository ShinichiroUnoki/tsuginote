/**
 * 認証コンテキスト — ユーザー状態管理
 * zustandでグローバルに認証状態を保持
 */
"use client";

import { create } from "zustand";
import { api, clearTokens, setTokens } from "@/lib/api";

/** ユーザー型定義 */
export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  /** 初期化 — マウント時にトークン検証 */
  initialize: () => Promise<void>;

  /** ログイン */
  login: (email: string, password: string) => Promise<void>;

  /** サインアップ */
  signup: (name: string, email: string, password: string) => Promise<void>;

  /** ログアウト */
  logout: () => void;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  initialize: async () => {
    try {
      const user = await api.get<User>("/auth/me");
      set({ user, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (email, password) => {
    const data = await api.post<{
      access_token: string;
      refresh_token: string;
      user: User;
    }>("/auth/login", { email, password });

    setTokens(data.access_token, data.refresh_token);
    set({ user: data.user, isAuthenticated: true });
  },

  signup: async (name, email, password) => {
    const data = await api.post<{
      access_token: string;
      refresh_token: string;
      user: User;
    }>("/auth/signup", { name, email, password });

    setTokens(data.access_token, data.refresh_token);
    set({ user: data.user, isAuthenticated: true });
  },

  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false });
  },
}));
