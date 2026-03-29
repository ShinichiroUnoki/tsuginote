/**
 * メンバー管理ページ — ワークスペースメンバーの招待・管理
 */
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { Users, UserPlus, Mail, Trash2, Shield, Loader2 } from "lucide-react";

interface Member {
  id: string;
  user: { id: string; name: string; email: string };
  role: string;
  joined_at: string;
}

export default function MembersPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [isInviting, setIsInviting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const wid = "default";
    api
      .get<Member[]>(`/workspaces/${wid}/members`)
      .then(setMembers)
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const handleInvite = async () => {
    if (!inviteEmail.trim()) return;
    setIsInviting(true);
    try {
      const wid = "default";
      await api.post(`/workspaces/${wid}/invite`, { email: inviteEmail });
      setInviteEmail("");
      // メンバーリスト再取得
      const updated = await api.get<Member[]>(`/workspaces/${wid}/members`);
      setMembers(updated);
    } catch {
      // TODO: エラーハンドリング
    } finally {
      setIsInviting(false);
    }
  };

  const roleLabel: Record<string, string> = {
    owner: "オーナー",
    admin: "管理者",
    member: "メンバー",
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">メンバー管理</h1>
        <p className="mt-1 text-sm text-slate-400">
          ワークスペースメンバーの招待・管理
        </p>
      </div>

      {/* 招待フォーム */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <UserPlus className="h-5 w-5 text-blue-400" />
            メンバー招待
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              type="email"
              placeholder="メールアドレスを入力"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleInvite()}
              className="border-slate-600 bg-slate-700/50 text-white placeholder:text-slate-500"
            />
            <Button
              onClick={handleInvite}
              disabled={isInviting || !inviteEmail.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isInviting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Mail className="mr-1 h-4 w-4" />
              )}
              招待
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* メンバーリスト */}
      <Card className="border-slate-700 bg-slate-800/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Users className="h-5 w-5 text-blue-400" />
            メンバー一覧
            <Badge variant="secondary" className="ml-2">
              {members.length}人
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          ) : (
            <div className="divide-y divide-slate-700">
              {members.map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between py-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-700 text-sm font-medium text-white">
                      {m.user.name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        {m.user.name}
                      </p>
                      <p className="text-xs text-slate-500">{m.user.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant="outline"
                      className="border-slate-600 text-xs text-slate-400"
                    >
                      <Shield className="mr-1 h-3 w-3" />
                      {roleLabel[m.role] ?? m.role}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
