/**
 * ドキュメント詳細・編集ページ — Markdownエディタ付き
 */
"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { ArrowLeft, Save, Sparkles, History, Loader2 } from "lucide-react";

/** SSR無効化 — Markdownエディタはクライアントのみ */
const MDEditor = dynamic(() => import("@uiw/react-md-editor"), { ssr: false });

interface DocumentDetail {
  id: string;
  title: string;
  content: string;
  category: string;
  is_ai_generated: boolean;
  created_at: string;
  updated_at: string;
  author: { name: string };
  tags: string[];
}

export default function DocumentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();

  const [doc, setDoc] = useState<DocumentDetail | null>(null);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (id === "new") {
      setDoc(null);
      setIsLoading(false);
      return;
    }
    const wid = "default";
    api
      .get<DocumentDetail>(`/workspaces/${wid}/documents/${id}`)
      .then((data) => {
        setDoc(data);
        setTitle(data.title);
        setContent(data.content);
      })
      .catch(() => router.push("/documents"))
      .finally(() => setIsLoading(false));
  }, [id, router]);

  const handleSave = async () => {
    setIsSaving(true);
    const wid = "default";
    try {
      if (id === "new") {
        const created = await api.post<DocumentDetail>(
          `/workspaces/${wid}/documents`,
          { title, content, category: "general" },
        );
        router.push(`/documents/${created.id}`);
      } else {
        await api.put(`/workspaces/${wid}/documents/${id}`, { title, content });
      }
    } catch {
      // TODO: エラートースト表示
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/documents")}
            className="text-slate-400 hover:text-white"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            戻る
          </Button>
          {doc?.is_ai_generated && (
            <Badge className="bg-emerald-500/20 text-emerald-400">
              <Sparkles className="mr-1 h-3 w-3" />
              AI生成
            </Badge>
          )}
        </div>
        <div className="flex gap-2">
          {id !== "new" && (
            <Button
              variant="outline"
              size="sm"
              className="border-slate-600 text-slate-300"
            >
              <History className="mr-1 h-4 w-4" />
              変更履歴
            </Button>
          )}
          <Button
            size="sm"
            onClick={handleSave}
            disabled={isSaving}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isSaving ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-1 h-4 w-4" />
            )}
            保存
          </Button>
        </div>
      </div>

      {/* タイトル */}
      <Input
        placeholder="ドキュメントタイトル"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="border-none bg-transparent text-2xl font-bold text-white placeholder:text-slate-600 focus-visible:ring-0"
      />

      {/* Markdownエディタ */}
      <div data-color-mode="dark">
        <MDEditor
          value={content}
          onChange={(val) => setContent(val || "")}
          height={500}
          preview="live"
        />
      </div>
    </div>
  );
}
