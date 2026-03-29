/**
 * ナレッジ検索ページ — セマンティック検索 + Q&A
 */
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import {
  Search,
  FileText,
  Loader2,
  MessageSquare,
  Sparkles,
} from "lucide-react";
import Link from "next/link";

interface SearchResult {
  document_id: string;
  title: string;
  snippet: string;
  score: number;
}

interface QaAnswer {
  answer: string;
  sources: { document_id: string; title: string }[];
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [answer, setAnswer] = useState<QaAnswer | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [mode, setMode] = useState<"search" | "qa">("search");

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    setResults([]);
    setAnswer(null);

    const wid = "default";
    try {
      if (mode === "search") {
        const data = await api.post<SearchResult[]>(
          `/workspaces/${wid}/ai/search`,
          { query },
        );
        setResults(data);
      } else {
        const data = await api.post<QaAnswer>(
          `/workspaces/${wid}/ai/ask`,
          { query },
        );
        setAnswer(data);
      }
    } catch {
      // TODO: エラーハンドリング
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">ナレッジ検索</h1>
        <p className="mt-1 text-sm text-slate-400">
          AIが業務知識を意味ベースで検索・回答します
        </p>
      </div>

      {/* 検索フォーム */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardContent className="space-y-4 pt-6">
          {/* モード切替 */}
          <div className="flex gap-2">
            <Button
              variant={mode === "search" ? "default" : "outline"}
              size="sm"
              onClick={() => setMode("search")}
              className={mode === "search" ? "bg-blue-600" : "border-slate-600 text-slate-300"}
            >
              <Search className="mr-1 h-4 w-4" />
              ドキュメント検索
            </Button>
            <Button
              variant={mode === "qa" ? "default" : "outline"}
              size="sm"
              onClick={() => setMode("qa")}
              className={mode === "qa" ? "bg-blue-600" : "border-slate-600 text-slate-300"}
            >
              <MessageSquare className="mr-1 h-4 w-4" />
              AIに質問
            </Button>
          </div>

          {/* 検索入力 */}
          <div className="flex gap-2">
            <Input
              placeholder={
                mode === "search"
                  ? "ドキュメントを検索..."
                  : "業務について質問してください..."
              }
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="border-slate-600 bg-slate-700/50 text-white placeholder:text-slate-500"
            />
            <Button
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isSearching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 検索結果 */}
      {results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-slate-400">
            {results.length}件の結果
          </p>
          {results.map((r) => (
            <Link key={r.document_id} href={`/documents/${r.document_id}`}>
              <Card className="border-slate-700 bg-slate-800/50 transition-colors hover:bg-slate-800">
                <CardContent className="py-4">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-blue-400" />
                    <h3 className="font-medium text-white">{r.title}</h3>
                    <Badge variant="secondary" className="ml-auto text-xs">
                      {Math.round(r.score * 100)}% 一致
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm text-slate-400">{r.snippet}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Q&A回答 */}
      {answer && (
        <Card className="border-blue-500/30 bg-slate-800/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Sparkles className="h-5 w-5 text-emerald-400" />
              AIの回答
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md bg-slate-900 p-4 text-sm text-slate-300 whitespace-pre-wrap">
              {answer.answer}
            </div>
            {answer.sources.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium text-slate-500">
                  参照ドキュメント:
                </p>
                <div className="flex flex-wrap gap-2">
                  {answer.sources.map((s) => (
                    <Link key={s.document_id} href={`/documents/${s.document_id}`}>
                      <Badge variant="outline" className="border-slate-600 text-slate-400 hover:text-white">
                        <FileText className="mr-1 h-3 w-3" />
                        {s.title}
                      </Badge>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
