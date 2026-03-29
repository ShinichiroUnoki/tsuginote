/**
 * CTAセクション — 最終アクション誘導
 */
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function CtaSection() {
  return (
    <section className="bg-slate-950 py-20">
      <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-white sm:text-4xl">
          属人化を今日から解消しませんか？
        </h2>
        <p className="mt-4 text-lg text-slate-400">
          無料プランで今すぐお試しいただけます。クレジットカード不要。
        </p>
        <div className="mt-8">
          <Link href="/signup">
            <Button size="lg" className="bg-blue-600 px-10 text-base hover:bg-blue-700">
              無料で始める
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </section>
  );
}
