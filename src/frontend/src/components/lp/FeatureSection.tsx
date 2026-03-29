/**
 * 機能紹介セクション — 3つの主要機能を訴求
 */
import { Card, CardContent } from "@/components/ui/card";
import { Sparkles, Search, CheckSquare } from "lucide-react";

const features = [
  {
    icon: Sparkles,
    title: "AI自動ドキュメント生成",
    description:
      "業務内容を入力するだけで、AIが構造化されたドキュメントを自動生成。手間なく知識をストック。",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  {
    icon: Search,
    title: "セマンティック検索",
    description:
      "キーワード一致ではなく「意味」で検索。「あの件どうだっけ？」という曖昧な質問にもAIが的確に回答。",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  {
    icon: CheckSquare,
    title: "引き継ぎチェックリスト",
    description:
      "退職・異動時に必要な引き継ぎ項目をAIが自動提案。漏れのない業務移管を実現。",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
  },
];

export function FeatureSection() {
  return (
    <section className="bg-slate-950 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            TsugiNoteの3つの機能
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            AIの力で、業務知識の継承を自動化します
          </p>
        </div>

        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card
              key={feature.title}
              className="border-slate-700 bg-slate-800/50 transition-transform hover:scale-[1.02]"
            >
              <CardContent className="pt-6">
                <div
                  className={`mb-4 inline-flex rounded-lg p-3 ${feature.bg}`}
                >
                  <feature.icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <h3 className="text-lg font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm text-slate-400">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
