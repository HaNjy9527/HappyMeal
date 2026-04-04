import { Navigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <main className="auth-state-screen">
        <section className="auth-state-card">
          <p className="eyebrow">HappyMeal</p>
          <h1>登入狀態確認中</h1>
          <p>正在確認你的 session，確認完成後會自動進入主流程。</p>
        </section>
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
