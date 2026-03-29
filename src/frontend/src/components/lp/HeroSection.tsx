/**
 * ヒーローセクション — メインキャッチコピーとCTA
 */
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, FileText } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-slate-950 py-24 sm:py-32">
      {/* 背景グラデーション */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-600/10 via-transparent to-transparent" />

      <div className="relative mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
        {/* バッジ */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-sm text-blue-400">
          <FileText className="h-4 w-4" />
          業務知識の継承をAIで自動化
        </div>

        {/* メインコピー */}
        <h1 className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
          退職しても、
          <br />
          <span className="text-blue-500">業務知識は残る。</span>
        </h1>

        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400 sm:text-xl">
          AIが業務知識を自動でドキュメント化。
          セマンティック検索と引き継ぎチェックリストで、属人化を解消します。
        </p>

        {/* CTA */}
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link href="/signup">
            <Button size="lg" className="bg-blue-600 px-8 text-base hover:bg-blue-700">
              無料で始める
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <Link href="/pricing">
            <Button size="lg" variant="outline" className="border-slate-700 px-8 text-base text-slate-300 hover:bg-slate-800">
              料金プランを見る
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
