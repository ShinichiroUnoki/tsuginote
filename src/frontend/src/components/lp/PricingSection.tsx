/**
 * 料金プランセクション — 4プランの比較表示
 */
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";

/** プランデータ定義 */
export const plans = [
  {
    name: "Free",
    price: "¥0",
    period: "永久無料",
    description: "個人での試用に",
    features: [
      "1ワークスペース",
      "ドキュメント10件まで",
      "AI生成 月5回",
      "基本検索",
    ],
    cta: "無料で始める",
    highlighted: false,
  },
  {
    name: "Team",
    price: "¥4,980",
    period: "月額 / ワークスペース",
    description: "小規模チーム向け",
    features: [
      "メンバー10人まで",
      "ドキュメント無制限",
      "AI生成 月100回",
      "セマンティック検索",
      "チェックリスト",
      "バージョン履歴",
    ],
    cta: "無料で始める",
    highlighted: true,
  },
  {
    name: "Business",
    price: "¥14,800",
    period: "月額 / ワークスペース",
    description: "成長企業向け",
    features: [
      "メンバー50人まで",
      "ドキュメント無制限",
      "AI生成 月500回",
      "高精度セマンティック検索",
      "カスタムテンプレート",
      "API連携",
      "優先サポート",
    ],
    cta: "無料で始める",
    highlighted: false,
  },
  {
    name: "Enterprise",
    price: "¥29,800",
    period: "月額 / ワークスペース",
    description: "大規模組織向け",
    features: [
      "メンバー無制限",
      "ドキュメント無制限",
      "AI生成 無制限",
      "オンプレミス対応",
      "SSO / SAML",
      "監査ログ",
      "SLA保証",
      "専任サポート",
    ],
    cta: "お問い合わせ",
    highlighted: false,
  },
];

export function PricingSection() {
  return (
    <section className="bg-slate-900 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            料金プラン
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            チームの規模に合わせて最適なプランをお選びください
          </p>
        </div>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {plans.map((plan) => (
            <Card
              key={plan.name}
              className={`relative border-slate-700 bg-slate-800/50 ${
                plan.highlighted ? "ring-2 ring-blue-500" : ""
              }`}
            >
              {plan.highlighted && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600">
                  人気
                </Badge>
              )}
              <CardHeader>
                <CardTitle className="text-white">{plan.name}</CardTitle>
                <div className="mt-2">
                  <span className="text-3xl font-bold text-white">
                    {plan.price}
                  </span>
                  <span className="ml-2 text-sm text-slate-400">
                    {plan.period}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-400">
                  {plan.description}
                </p>
              </CardHeader>
              <CardContent>
                <ul className="mb-6 space-y-2">
                  {plan.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-center gap-2 text-sm text-slate-300"
                    >
                      <Check className="h-4 w-4 shrink-0 text-blue-400" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link href="/signup" className="block">
                  <Button
                    className={`w-full ${
                      plan.highlighted
                        ? "bg-blue-600 hover:bg-blue-700"
                        : "bg-slate-700 hover:bg-slate-600"
                    }`}
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
