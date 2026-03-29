/**
 * 課題提示セクション — 属人化の3つの問題点を訴求
 */
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, Clock, UserX } from "lucide-react";

const problems = [
  {
    icon: UserX,
    title: "突然の退職で知識が消失",
    description:
      "担当者が退職すると、暗黙知やノウハウが一瞬で失われます。後任者はゼロから手探りで業務を覚えることに。",
  },
  {
    icon: Clock,
    title: "引き継ぎに膨大な時間",
    description:
      "口頭やチャットでの引き継ぎは漏れが多く、何度も同じ質問が繰り返されます。引き継ぎ期間が長期化し、生産性が低下。",
  },
  {
    icon: AlertTriangle,
    title: "ドキュメントが更新されない",
    description:
      "手動でのドキュメント作成は面倒で後回しに。古い情報が残り続け、かえって混乱を招きます。",
  },
];

export function ProblemSection() {
  return (
    <section className="bg-slate-900 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            こんな課題、ありませんか？
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            属人化は組織の成長を阻むサイレントキラーです
          </p>
        </div>

        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {problems.map((problem) => (
            <Card
              key={problem.title}
              className="border-slate-700 bg-slate-800/50"
            >
              <CardContent className="pt-6">
                <problem.icon className="mb-4 h-10 w-10 text-red-400" />
                <h3 className="text-lg font-semibold text-white">
                  {problem.title}
                </h3>
                <p className="mt-2 text-sm text-slate-400">
                  {problem.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
