/**
 * プラン・請求ページ — 現在のプラン表示・プラン変更
 */
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { CreditCard, Check, ArrowUpRight, Loader2 } from "lucide-react";

interface Subscription {
  plan: string;
  status: string;
  current_period_end: string;
}

const planOrder = ["free", "team", "business", "enterprise"];

const planDetails: Record<string, { name: string; price: string }> = {
  free: { name: "Free", price: "¥0" },
  team: { name: "Team", price: "¥4,980/月" },
  business: { name: "Business", price: "¥14,800/月" },
  enterprise: { name: "Enterprise", price: "¥29,800/月" },
};

export default function BillingPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .get<Subscription>("/billing/subscription")
      .then(setSubscription)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const handleUpgrade = async (plan: string) => {
    try {
      const data = await api.post<{ url: string }>("/billing/checkout", {
        plan,
      });
      window.location.href = data.url;
    } catch {
      // TODO: エラーハンドリング
    }
  };

  const handleManage = async () => {
    try {
      const data = await api.post<{ url: string }>("/billing/portal");
      window.location.href = data.url;
    } catch {
      // TODO: エラーハンドリング
    }
  };

  const currentPlan = subscription?.plan ?? "free";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">プラン・請求</h1>
        <p className="mt-1 text-sm text-slate-400">
          サブスクリプションと請求情報の管理
        </p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      ) : (
        <>
          {/* 現在のプラン */}
          <Card className="border-slate-700 bg-slate-800/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <CreditCard className="h-5 w-5 text-blue-400" />
                現在のプラン
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-bold text-white">
                  {planDetails[currentPlan]?.name ?? currentPlan}
                </span>
                <Badge className="bg-blue-500/20 text-blue-400">
                  {subscription?.status === "active" ? "有効" : "無料"}
                </Badge>
              </div>
              <p className="text-sm text-slate-400">
                {planDetails[currentPlan]?.price ?? "¥0"}
              </p>
              {subscription?.current_period_end && (
                <p className="text-xs text-slate-500">
                  次回更新日:{" "}
                  {new Date(subscription.current_period_end).toLocaleDateString("ja-JP")}
                </p>
              )}
              {currentPlan !== "free" && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleManage}
                  className="border-slate-600 text-slate-300"
                >
                  <ArrowUpRight className="mr-1 h-4 w-4" />
                  Stripe管理画面
                </Button>
              )}
            </CardContent>
          </Card>

          {/* プラン一覧 */}
          <div className="grid gap-4 sm:grid-cols-2">
            {planOrder.map((plan) => {
              const detail = planDetails[plan];
              const isCurrent = plan === currentPlan;
              const isUpgrade =
                planOrder.indexOf(plan) > planOrder.indexOf(currentPlan);

              return (
                <Card
                  key={plan}
                  className={`border-slate-700 bg-slate-800/50 ${
                    isCurrent ? "ring-2 ring-blue-500" : ""
                  }`}
                >
                  <CardContent className="pt-6">
                    <h3 className="text-lg font-semibold text-white">
                      {detail.name}
                    </h3>
                    <p className="mt-1 text-xl font-bold text-white">
                      {detail.price}
                    </p>
                    <div className="mt-4">
                      {isCurrent ? (
                        <Badge className="bg-blue-500/20 text-blue-400">
                          <Check className="mr-1 h-3 w-3" />
                          現在のプラン
                        </Badge>
                      ) : isUpgrade ? (
                        <Button
                          size="sm"
                          onClick={() => handleUpgrade(plan)}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          アップグレード
                        </Button>
                      ) : (
                        <span className="text-xs text-slate-500">
                          ダウングレードはサポートにお問い合わせ
                        </span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
