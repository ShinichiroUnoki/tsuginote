/**
 * サイドバー — 認証後画面のナビゲーション
 * 各機能へのリンクとワークスペース情報を表示
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  FileText,
  Sparkles,
  Search,
  CheckSquare,
  Settings,
  Users,
  CreditCard,
  User,
} from "lucide-react";

/** ナビゲーション項目定義 */
const mainNav = [
  { href: "/dashboard", label: "ダッシュボード", icon: LayoutDashboard },
  { href: "/documents", label: "ドキュメント", icon: FileText },
  { href: "/ai/generate", label: "AI生成", icon: Sparkles },
  { href: "/search", label: "ナレッジ検索", icon: Search },
  { href: "/checklists", label: "チェックリスト", icon: CheckSquare },
];

const settingsNav = [
  { href: "/settings/members", label: "メンバー管理", icon: Users },
  { href: "/settings/billing", label: "プラン・請求", icon: CreditCard },
  { href: "/settings/profile", label: "プロフィール", icon: User },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-800 bg-slate-900">
      {/* ロゴ */}
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-6">
        <FileText className="h-6 w-6 text-blue-500" />
        <span className="text-lg font-bold text-white">TsugiNote</span>
      </div>

      {/* メインナビ */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {mainNav.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white",
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* 設定ナビ */}
      <div className="border-t border-slate-800 px-3 py-4">
        <p className="mb-2 px-3 text-xs font-medium uppercase text-slate-500">
          <Settings className="mr-1 inline h-3 w-3" />
          設定
        </p>
        {settingsNav.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white",
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
