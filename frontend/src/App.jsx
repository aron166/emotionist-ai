import { Outlet } from "react-router-dom";

export default function App() {
  return (
    <>
      <div className="grain" />
      <div className="chrome" />
      <div className="glow" />

      <header className="topbar">
        <div className="hero">
          <span className="eyebrow">Enterprise Conversation Training</span>
          <div className="brand">EMOTIONIST<span className="dot">.AI</span></div>
          <div className="brand-sub">
            Practice partner that <em>feels</em> - rehearse a hard conversation against an
            emotionally-reactive counterpart whose mood persists until you handle it well.
          </div>
        </div>
      </header>

      <main className="wrap">
        <Outlet />
      </main>
    </>
  );
}
