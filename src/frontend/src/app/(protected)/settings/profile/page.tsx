/**
 * プロフィール設定ページ — ユーザー情報の表示・編集
 */
"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { User, Save, Loader2 } from "lucide-react";

export default function ProfilePage() {
  const { user, initialize } = useAuth();
  const [name, setName] = useState(user?.name ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  const handleSave = async () => {
    setIsSaving(true);
    setMessage("");
    try {
      await api.put("/auth/me", { name });
      await initialize();
      setMessage("プロフィールを更新しました");
    } catch {
      setMessage("更新に失敗しました");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">プロフィール</h1>
        <p className="mt-1 text-sm text-slate-400">
          アカウント情報の管理
        </p>
      </div>

      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <User className="h-5 w-5 text-blue-400" />
            基本情報
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {message && (
            <div
              className={`rounded-md p-3 text-sm ${
                message.includes("失敗")
                  ? "bg-red-500/10 text-red-400"
                  : "bg-emerald-500/10 text-emerald-400"
              }`}
            >
              {message}
            </div>
          )}

          <div className="space-y-2">
            <Label className="text-slate-300">メールアドレス</Label>
            <Input
              value={user?.email ?? ""}
              disabled
              className="border-slate-600 bg-slate-700/30 text-slate-400"
            />
            <p className="text-xs text-slate-500">
              メールアドレスは変更できません
            </p>
          </div>

          <div className="space-y-2">
            <Label className="text-slate-300">名前</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="border-slate-600 bg-slate-700/50 text-white"
            />
          </div>

          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isSaving ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            保存
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
