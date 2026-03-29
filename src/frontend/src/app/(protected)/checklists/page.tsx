/**
 * チェックリスト一覧ページ — 引き継ぎチェックリストの管理
 */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { CheckSquare, Plus, Calendar, User } from "lucide-react";

interface Checklist {
  id: string;
  title: string;
  template_type: string;
  created_at: string;
  creator: { name: string };
  total_items: number;
  completed_items: number;
}

export default function ChecklistsPage() {
  const [checklists, setChecklists] = useState<Checklist[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const wid = "default";
    api
      .get<Checklist[]>(`/workspaces/${wid}/checklists`)
      .then(setChecklists)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">チェックリスト</h1>
          <p className="mt-1 text-sm text-slate-400">
            引き継ぎチェックリストの管理
          </p>
        </div>
        <Button className="bg-blue-600 hover:bg-blue-700">
          <Plus className="mr-2 h-4 w-4" />
          新規作成
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        </div>
      ) : checklists.length === 0 ? (
        <Card className="border-slate-700 bg-slate-800/50">
          <CardContent className="py-12 text-center">
            <CheckSquare className="mx-auto h-12 w-12 text-slate-600" />
            <p className="mt-4 text-slate-400">
              まだチェックリストがありません
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {checklists.map((cl) => {
            const progress =
              cl.total_items > 0
                ? Math.round((cl.completed_items / cl.total_items) * 100)
                : 0;
            return (
              <Link key={cl.id} href={`/checklists/${cl.id}`}>
                <Card className="border-slate-700 bg-slate-800/50 transition-colors hover:bg-slate-800">
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <CheckSquare className="h-5 w-5 text-purple-400" />
                        <div>
                          <h3 className="font-medium text-white">{cl.title}</h3>
                          <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {cl.creator.name}
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(cl.created_at).toLocaleDateString("ja-JP")}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <p className="text-sm font-medium text-white">
                            {cl.completed_items}/{cl.total_items}
                          </p>
                          <p className="text-xs text-slate-500">完了</p>
                        </div>
                        <Badge
                          className={
                            progress === 100
                              ? "bg-emerald-500/20 text-emerald-400"
                              : "bg-amber-500/20 text-amber-400"
                          }
                        >
                          {progress}%
                        </Badge>
                      </div>
                    </div>
                    {/* プログレスバー */}
                    <div className="mt-3 h-1.5 rounded-full bg-slate-700">
                      <div
                        className="h-1.5 rounded-full bg-blue-500 transition-all"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
