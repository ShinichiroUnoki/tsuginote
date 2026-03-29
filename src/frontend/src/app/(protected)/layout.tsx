/**
 * 認証必要ページレイアウト — ProtectedRouteでガード
 */
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}
