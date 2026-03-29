/**
 * ドキュメント一覧ページ — 検索・フィルタ・一覧表示
 */
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import {
  FileText,
  Plus,
  Search,
  Sparkles,
  Calendar,
  Trash2,
} from "lucide-react";

interface Document {
  id: string;
  title: string;
  category: string;
  is_ai_generated: boolean;
  created_at: string;
  updated_at: string;
  author: { name: string };
  tags: string[];
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const wid = "default";
    api
      .get<Document[]>(`/workspaces/${wid}/documents`)
      .then(setDocuments)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  /** ローカルフィルタリング */
  const filtered = documents.filter(
    (doc) =>
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.category.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">ドキュメント</h1>
          <p className="mt-1 text-sm text-slate-400">
            業務知識ドキュメントの管理
          </p>
        </div>
        <Link href="/documents/new">
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="mr-2 h-4 w-4" />
            新規作成
          </Button>
        </Link>
      </div>

      {/* 検索バー */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <Input
          placeholder="ドキュメントを検索..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="border-slate-600 bg-slate-800/50 pl-10 text-white placeholder:text-slate-500"
        />
      </div>

      {/* ドキュメントリスト */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
        </div>
      ) : filtered.length === 0 ? (
        <Card className="border-slate-700 bg-slate-800/50">
          <CardContent className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-slate-600" />
            <p className="mt-4 text-slate-400">
              {searchQuery
                ? "検索結果がありません"
                : "まだドキュメントがありません"}
            </p>
            {!searchQuery && (
              <Link href="/ai/generate" className="mt-4 inline-block">
                <Button className="bg-blue-600 hover:bg-blue-700">
                  <Sparkles className="mr-2 h-4 w-4" />
                  AIで最初のドキュメントを生成
                </Button>
              </Link>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {filtered.map((doc) => (
            <Link key={doc.id} href={`/documents/${doc.id}`}>
              <Card className="border-slate-700 bg-slate-800/50 transition-colors hover:bg-slate-800">
                <CardContent className="flex items-center gap-4 py-4">
                  <FileText className="h-8 w-8 shrink-0 text-blue-400" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="truncate font-medium text-white">
                        {doc.title}
                      </h3>
                      {doc.is_ai_generated && (
                        <Badge className="shrink-0 bg-emerald-500/20 text-emerald-400">
                          <Sparkles className="mr-1 h-3 w-3" />
                          AI生成
                        </Badge>
                      )}
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
                      <span>{doc.author.name}</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(doc.updated_at).toLocaleDateString("ja-JP")}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {doc.category}
                      </Badge>
                    </div>
                    {doc.tags.length > 0 && (
                      <div className="mt-1.5 flex gap-1">
                        {doc.tags.map((tag) => (
                          <Badge
                            key={tag}
                            variant="outline"
                            className="border-slate-600 text-xs text-slate-400"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
