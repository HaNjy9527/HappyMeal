import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export default function App() {
  return (
    <main className="app-shell">
      <section className="hero-card">
        <p className="eyebrow">HappyMeal MVP</p>
        <h1>Step 1 本地 Docker 環境已就緒</h1>
        <p className="lead">
          目前前端使用 Vite 開發模式，後續會接上登入、分析與歷史流程。
        </p>
        <dl className="status-grid">
          <div>
            <dt>Frontend</dt>
            <dd>Vite + React + TypeScript</dd>
          </div>
          <div>
            <dt>Backend</dt>
            <dd>{apiBaseUrl}</dd>
          </div>
          <div>
            <dt>Step 1</dt>
            <dd>Docker + Alembic 骨架</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
