/**
 * 料金ページ — 4プランの詳細比較表
 */
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, X } from "lucide-react";
import { plans } from "@/components/lp/PricingSection";

/** 機能比較マトリクス */
const comparisonFeatures = [
  { name: "ワークスペース数", free: "1", team: "無制限", business: "無制限", enterprise: "無制限" },
  { name: "メンバー数", free: "1人", team: "10人", business: "50人", enterprise: "無制限" },
  { name: "ドキュメント数", free: "10件", team: "無制限", business: "無制限", enterprise: "無制限" },
  { name: "AI生成回数/月", free: "5回", team: "100回", business: "500回", enterprise: "無制限" },
  { name: "セマンティック検索", free: false, team: true, business: true, enterprise: true },
  { name: "チェックリスト", free: false, team: true, business: true, enterprise: true },
  { name: "バージョン履歴", free: false, team: true, business: true, enterprise: true },
  { name: "カスタムテンプレート", free: false, team: false, business: true, enterprise: true },
  { name: "API連携", free: false, team: false, business: true, enterprise: true },
  { name: "SSO / SAML", free: false, team: false, business: false, enterprise: true },
  { name: "監査ログ", free: false, team: false, business: false, enterprise: true },
  { name: "SLA保証", free: false, team: false, business: false, enterprise: true },
  { name: "優先サポート", free: false, team: false, business: true, enterprise: true },
  { name: "専任サポート", free: false, team: false, business: false, enterprise: true },
];

function CellValue({ value }: { value: string | boolean }) {
  if (typeof value === "string") {
    return <span className="text-sm text-slate-300">{value}</span>;
  }
  return value ? (
    <Check className="mx-auto h-4 w-4 text-blue-400" />
  ) : (
    <X className="mx-auto h-4 w-4 text-slate-600" />
  );
}

export default function PricingPage() {
  return (
    <div className="py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-white">料金プラン</h1>
          <p className="mt-4 text-lg text-slate-400">
            チームの規模に合わせて最適なプランをお選びください
          </p>
        </div>

        {/* プランカード */}
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
                  <span className="text-3xl font-bold text-white">{plan.price}</span>
                  <span className="ml-2 text-sm text-slate-400">{plan.period}</span>
                </div>
              </CardHeader>
              <CardContent>
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

        {/* 比較表 */}
        <div className="mt-16">
          <h2 className="mb-8 text-center text-2xl font-bold text-white">
            機能比較
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
                    機能
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-slate-400">
                    Free
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-blue-400">
                    Team
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-slate-400">
                    Business
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-slate-400">
                    Enterprise
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparisonFeatures.map((feature) => (
                  <tr
                    key={feature.name}
                    className="border-b border-slate-800 hover:bg-slate-800/30"
                  >
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {feature.name}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <CellValue value={feature.free} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <CellValue value={feature.team} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <CellValue value={feature.business} />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <CellValue value={feature.enterprise} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
