import { useId, useState } from "react";

const EyeIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1.5 12S5 5 12 5s10.5 7 10.5 7-3.5 7-10.5 7S1.5 12 1.5 12Z" />
    <circle cx="12" cy="12" r="3.2" />
  </svg>
);

const EyeOffIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 3l18 18" />
    <path d="M10.6 5.2A10.6 10.6 0 0 1 12 5c7 0 10.5 7 10.5 7a15.6 15.6 0 0 1-3.4 4.3M6.6 6.6C3.7 8.4 1.5 12 1.5 12s3.5 7 10.5 7c1.4 0 2.6-.2 3.7-.6" />
    <path d="M9.5 9.6a3.2 3.2 0 0 0 4.4 4.5" />
  </svg>
);

export default function PasswordField({ id, label, value, onChange, placeholder, autoComplete }) {
  const [visible, setVisible] = useState(false);
  const generatedId = useId();
  const inputId = id || generatedId;

  return (
    <div className="auth-field">
      <label className="auth-label" htmlFor={inputId}>
        {label}
      </label>
      <div className="auth-password-wrap">
        <input
          id={inputId}
          className="auth-input"
          type={visible ? "text" : "password"}
          placeholder={placeholder}
          value={value}
          autoComplete={autoComplete}
          onChange={(e) => onChange(e.target.value)}
          required
        />
        <button
          type="button"
          className="auth-password-toggle"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? "Hide password" : "Show password"}
          tabIndex={-1}
        >
          {visible ? <EyeOffIcon /> : <EyeIcon />}
        </button>
      </div>
    </div>
  );
}
