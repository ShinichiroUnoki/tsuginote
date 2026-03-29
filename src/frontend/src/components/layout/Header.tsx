/**
 * 共通ヘッダー — LP・公開ページ用
 * ロゴ・ナビゲーション・CTA配置
 */
"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FileText } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* ロゴ */}
        <Link href="/" className="flex items-center gap-2">
          <FileText className="h-7 w-7 text-blue-500" />
          <span className="text-xl font-bold text-white">TsugiNote</span>
        </Link>

        {/* ナビゲーション */}
        <nav className="hidden items-center gap-6 md:flex">
          <Link
            href="/pricing"
            className="text-sm text-slate-300 transition-colors hover:text-white"
          >
            料金プラン
          </Link>
          <Link href="/login">
            <Button variant="ghost" className="text-slate-300 hover:text-white">
              ログイン
            </Button>
          </Link>
          <Link href="/signup">
            <Button className="bg-blue-600 hover:bg-blue-700">
              無料で始める
            </Button>
          </Link>
        </nav>

        {/* モバイルメニュー — 簡易表示 */}
        <div className="flex items-center gap-2 md:hidden">
          <Link href="/login">
            <Button variant="ghost" size="sm" className="text-slate-300">
              ログイン
            </Button>
          </Link>
          <Link href="/signup">
            <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
              無料で始める
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
