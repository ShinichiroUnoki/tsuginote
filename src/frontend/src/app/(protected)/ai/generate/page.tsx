/**
 * AI生成ページ — 業務内容からドキュメントを自動生成
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { Sparkles, FileText, Loader2, ArrowRight } from "lucide-react";

/** 生成テンプレート選択肢 */
const templates = [
  { id: "procedure", label: "業務手順書", description: "ステップバイステップの業務手順" },
  { id: "knowledge", label: "ナレッジ記事", description: "業務ノウハウ・Tips" },
  { id: "handover", label: "引き継ぎ資料", description: "退職・異動時の引き継ぎ文書" },
  { id: "faq", label: "FAQ", description: "よくある質問と回答" },
];

interface GeneratedResult {
  id: string;
  title: string;
  content: string;
}

export default function AiGeneratePage() {
  const router = useRouter();
  const [inputText, setInputText] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState("procedure");
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<GeneratedResult | null>(null);

  const handleGenerate = async () => {
    if (!inputText.trim()) return;
    setIsGenerating(true);
    setResult(null);

    try {
      const wid = "default";
      const data = await api.post<GeneratedResult>(
        `/workspaces/${wid}/ai/generate`,
        { input_text: inputText, template_type: selectedTemplate },
      );
      setResult(data);
    } catch {
      // TODO: エラーハンドリング
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">AI ドキュメント生成</h1>
        <p className="mt-1 text-sm text-slate-400">
          業務内容を入力するだけで、構造化されたドキュメントを自動生成
        </p>
      </div>

      {/* 入力フォーム */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Sparkles className="h-5 w-5 text-emerald-400" />
            生成設定
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* テンプレート選択 */}
          <div className="space-y-2">
            <Label className="text-slate-300">テンプレート</Label>
            <div className="grid gap-2 sm:grid-cols-2">
              {templates.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTemplate(t.id)}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    selectedTemplate === t.id
                      ? "border-blue-500 bg-blue-500/10"
                      : "border-slate-600 bg-slate-700/30 hover:border-slate-500"
                  }`}
                >
                  <p className="text-sm font-medium text-white">{t.label}</p>
                  <p className="text-xs text-slate-400">{t.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* 入力テキスト */}
          <div className="space-y-2">
            <Label className="text-slate-300">業務内容の説明</Label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="例: 毎月の請求書処理の手順。経理システムにログインし、売上データをエクスポートして..."
              rows={6}
              className="w-full rounded-md border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !inputText.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {isGenerating ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            {isGenerating ? "生成中..." : "ドキュメントを生成"}
          </Button>
        </CardContent>
      </Card>

      {/* 生成結果 */}
      {result && (
        <Card className="border-emerald-500/30 bg-slate-800/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <FileText className="h-5 w-5 text-blue-400" />
              {result.title}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="prose prose-invert max-w-none rounded-md bg-slate-900 p-4 text-sm">
              <pre className="whitespace-pre-wrap text-slate-300">
                {result.content}
              </pre>
            </div>
            <Button
              onClick={() => router.push(`/documents/${result.id}`)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              ドキュメントとして編集
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
