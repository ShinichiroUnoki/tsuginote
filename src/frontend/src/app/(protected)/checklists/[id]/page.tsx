/**
 * チェックリスト詳細ページ — アイテムの表示・チェック操作
 */
"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import {
  ArrowLeft,
  CheckSquare,
  Square,
  FileText,
  Loader2,
} from "lucide-react";
import Link from "next/link";

interface ChecklistItem {
  id: string;
  description: string;
  is_completed: boolean;
  sort_order: number;
  document_id: string | null;
}

interface ChecklistDetail {
  id: string;
  title: string;
  template_type: string;
  created_at: string;
  items: ChecklistItem[];
}

export default function ChecklistDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [checklist, setChecklist] = useState<ChecklistDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const wid = "default";
    api
      .get<ChecklistDetail>(`/workspaces/${wid}/checklists/${id}`)
      .then(setChecklist)
      .catch(() => router.push("/checklists"))
      .finally(() => setIsLoading(false));
  }, [id, router]);

  const toggleItem = async (itemId: string, currentState: boolean) => {
    if (!checklist) return;
    const wid = "default";
    try {
      await api.put(
        `/workspaces/${wid}/checklists/${id}/items/${itemId}`,
        { is_completed: !currentState },
      );
      setChecklist({
        ...checklist,
        items: checklist.items.map((item) =>
          item.id === itemId
            ? { ...item, is_completed: !currentState }
            : item,
        ),
      });
    } catch {
      // TODO: エラーハンドリング
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!checklist) return null;

  const completed = checklist.items.filter((i) => i.is_completed).length;
  const total = checklist.items.length;
  const progress = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/checklists")}
          className="text-slate-400 hover:text-white"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          戻る
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">{checklist.title}</h1>
        <Badge
          className={
            progress === 100
              ? "bg-emerald-500/20 text-emerald-400"
              : "bg-blue-500/20 text-blue-400"
          }
        >
          {completed}/{total} 完了 ({progress}%)
        </Badge>
      </div>

      {/* プログレスバー */}
      <div className="h-2 rounded-full bg-slate-700">
        <div
          className="h-2 rounded-full bg-blue-500 transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* チェックリストアイテム */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardContent className="divide-y divide-slate-700 pt-2">
          {checklist.items
            .sort((a, b) => a.sort_order - b.sort_order)
            .map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-3 py-3"
              >
                <button
                  onClick={() => toggleItem(item.id, item.is_completed)}
                  className="shrink-0"
                >
                  {item.is_completed ? (
                    <CheckSquare className="h-5 w-5 text-blue-400" />
                  ) : (
                    <Square className="h-5 w-5 text-slate-500 hover:text-slate-300" />
                  )}
                </button>
                <span
                  className={`flex-1 text-sm ${
                    item.is_completed
                      ? "text-slate-500 line-through"
                      : "text-slate-300"
                  }`}
                >
                  {item.description}
                </span>
                {item.document_id && (
                  <Link href={`/documents/${item.document_id}`}>
                    <Badge variant="outline" className="border-slate-600 text-xs text-slate-400 hover:text-white">
                      <FileText className="mr-1 h-3 w-3" />
                      関連文書
                    </Badge>
                  </Link>
                )}
              </div>
            ))}
        </CardContent>
      </Card>
    </div>
  );
}
