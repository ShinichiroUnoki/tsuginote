/**
 * 公開ページレイアウト — ヘッダー + フッター付き
 */
import { Header } from "@/components/layout/Header";

export default function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Header />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-slate-800 bg-slate-900 py-8">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-slate-500">
          © 2026 TsugiNote. All rights reserved.
        </div>
      </footer>
    </>
  );
}
