/**
 * ダッシュボード — 統計情報・最近のアクティビティ・クイックアクション
 */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import {
  FileText,
  Sparkles,
  Search,
  CheckSquare,
  Plus,
  TrendingUp,
  Clock,
} from "lucide-react";

interface DashboardStats {
  total_documents: number;
  ai_generations_this_month: number;
  searches_this_month: number;
  active_checklists: number;
}

interface RecentActivity {
  id: string;
  type: "document_created" | "document_updated" | "ai_generated" | "search";
  title: string;
  created_at: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activities, setActivities] = useState<RecentActivity[]>([]);

  useEffect(() => {
    // TODO: ワークスペースIDをコンテキストから取得
    const wid = "default";
    api.get<DashboardStats>(`/workspaces/${wid}/dashboard/stats`).then(setStats).catch(() => {});
    api.get<RecentActivity[]>(`/workspaces/${wid}/dashboard/recent`).then(setActivities).catch(() => {});
  }, []);

  const statCards = [
    {
      label: "ドキュメント数",
      value: stats?.total_documents ?? 0,
      icon: FileText,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
    },
    {
      label: "AI生成（今月）",
      value: stats?.ai_generations_this_month ?? 0,
      icon: Sparkles,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
    },
    {
      label: "検索回数（今月）",
      value: stats?.searches_this_month ?? 0,
      icon: Search,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
    },
    {
      label: "進行中チェックリスト",
      value: stats?.active_checklists ?? 0,
      icon: CheckSquare,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
    },
  ];

  return (
    <div className="space-y-6">
      {/* ページヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">ダッシュボード</h1>
          <p className="mt-1 text-sm text-slate-400">
            ワークスペースの概要
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/documents">
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="mr-2 h-4 w-4" />
              ドキュメント作成
            </Button>
          </Link>
        </div>
      </div>

      {/* 統計カード */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Card key={stat.label} className="border-slate-700 bg-slate-800/50">
            <CardContent className="flex items-center gap-4 pt-6">
              <div className={`rounded-lg p-3 ${stat.bg}`}>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </div>
              <div>
                <p className="text-sm text-slate-400">{stat.label}</p>
                <p className="text-2xl font-bold text-white">{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* クイックアクション + 最近のアクティビティ */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* クイックアクション */}
        <Card className="border-slate-700 bg-slate-800/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <TrendingUp className="h-5 w-5 text-blue-400" />
              クイックアクション
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <Link href="/ai/generate">
              <Button variant="outline" className="w-full justify-start border-slate-600 text-slate-300 hover:bg-slate-700">
                <Sparkles className="mr-2 h-4 w-4 text-emerald-400" />
                AIでドキュメント生成
              </Button>
            </Link>
            <Link href="/search">
              <Button variant="outline" className="w-full justify-start border-slate-600 text-slate-300 hover:bg-slate-700">
                <Search className="mr-2 h-4 w-4 text-amber-400" />
                ナレッジ検索
              </Button>
            </Link>
            <Link href="/checklists">
              <Button variant="outline" className="w-full justify-start border-slate-600 text-slate-300 hover:bg-slate-700">
                <CheckSquare className="mr-2 h-4 w-4 text-purple-400" />
                チェックリスト作成
              </Button>
            </Link>
            <Link href="/settings/members">
              <Button variant="outline" className="w-full justify-start border-slate-600 text-slate-300 hover:bg-slate-700">
                <Plus className="mr-2 h-4 w-4 text-blue-400" />
                メンバー招待
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* 最近のアクティビティ */}
        <Card className="border-slate-700 bg-slate-800/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Clock className="h-5 w-5 text-blue-400" />
              最近のアクティビティ
            </CardTitle>
          </CardHeader>
          <CardContent>
            {activities.length === 0 ? (
              <p className="py-8 text-center text-sm text-slate-500">
                まだアクティビティがありません
              </p>
            ) : (
              <ul className="space-y-3">
                {activities.slice(0, 5).map((activity) => (
                  <li
                    key={activity.id}
                    className="flex items-center gap-3 rounded-md px-2 py-1.5"
                  >
                    <ActivityIcon type={activity.type} />
                    <div className="flex-1 truncate">
                      <p className="truncate text-sm text-slate-300">
                        {activity.title}
                      </p>
                      <p className="text-xs text-slate-500">
                        {new Date(activity.created_at).toLocaleDateString("ja-JP")}
                      </p>
                    </div>
                    <ActivityBadge type={activity.type} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ActivityIcon({ type }: { type: RecentActivity["type"] }) {
  switch (type) {
    case "document_created":
    case "document_updated":
      return <FileText className="h-4 w-4 shrink-0 text-blue-400" />;
    case "ai_generated":
      return <Sparkles className="h-4 w-4 shrink-0 text-emerald-400" />;
    case "search":
      return <Search className="h-4 w-4 shrink-0 text-amber-400" />;
  }
}

function ActivityBadge({ type }: { type: RecentActivity["type"] }) {
  const labels: Record<RecentActivity["type"], string> = {
    document_created: "作成",
    document_updated: "更新",
    ai_generated: "AI生成",
    search: "検索",
  };
  return (
    <Badge variant="secondary" className="shrink-0 text-xs">
      {labels[type]}
    </Badge>
  );
}
