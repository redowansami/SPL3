import "./auth.css";

export default function AuthLayout({ children }) {
  return (
    <div className="auth-screen">
      <div className="auth-bg" aria-hidden="true">
        <span className="auth-blob auth-blob-1" />
        <span className="auth-blob auth-blob-2" />
        <span className="auth-blob auth-blob-3" />
        <div className="auth-grid-overlay" />
      </div>

      <div className="auth-content">
        <div className="auth-brand">
          <span className="auth-logo-mark">A</span>
          <span className="auth-brand-name">ATLAS-Scan</span>
        </div>
        <div className="auth-card">{children}</div>
      </div>
    </div>
  );
}
