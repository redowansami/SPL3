import { useState } from "react";
import { register } from "../../api/authClient";
import PasswordField from "./PasswordField";

const USERNAME_PATTERN = /^[A-Za-z0-9_]{3,30}$/;
const SPECIAL_CHARS = /[!@#$%^&*()\-_=+[\]{};:,.<>/?]/;

function checkPasswordRules(password, confirmPassword) {
  return {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    digit: /\d/.test(password),
    special: SPECIAL_CHARS.test(password),
    match: password.length > 0 && password === confirmPassword,
  };
}

export default function RegisterPage({ onRegistered, onSwitchToLogin }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [touched, setTouched] = useState(false);

  const rules = checkPasswordRules(password, confirmPassword);
  const usernameValid = USERNAME_PATTERN.test(username);
  const allRulesPass = Object.values(rules).every(Boolean);

  const canSubmit =
    usernameValid && email.trim().length > 0 && allRulesPass && !submitting;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setTouched(true);
    setError(null);

    if (!canSubmit) {
      setError("Please fix the highlighted fields before continuing.");
      return;
    }

    setSubmitting(true);
    try {
      const data = await register({ username, email, password, confirmPassword });
      onRegistered(data.email);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <h1 className="auth-title">Create your account</h1>
      <p className="auth-subtitle">Sign up to start running ATLAS-Scan attacks.</p>

      {error && <div className="auth-alert auth-alert-error">{error}</div>}

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-username">
            Username
          </label>
          <input
            id="reg-username"
            className="auth-input"
            type="text"
            placeholder="yourname"
            value={username}
            autoComplete="username"
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          {touched && !usernameValid && (
            <span className="auth-checklist-item">3-30 characters: letters, digits, underscore only.</span>
          )}
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-email">
            Email
          </label>
          <input
            id="reg-email"
            className="auth-input"
            type="email"
            placeholder="you@example.com"
            value={email}
            autoComplete="email"
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <PasswordField
          id="reg-password"
          label="Password"
          placeholder="Create a strong password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
        />

        <PasswordField
          id="reg-confirm-password"
          label="Confirm password"
          placeholder="Re-enter your password"
          value={confirmPassword}
          onChange={setConfirmPassword}
          autoComplete="new-password"
        />

        {(password.length > 0 || confirmPassword.length > 0) && (
          <div className="auth-checklist">
            <ChecklistItem ok={rules.length} text="At least 8 characters" />
            <ChecklistItem ok={rules.upper} text="One uppercase letter" />
            <ChecklistItem ok={rules.lower} text="One lowercase letter" />
            <ChecklistItem ok={rules.digit} text="One digit" />
            <ChecklistItem ok={rules.special} text="One special character" />
            <ChecklistItem ok={rules.match} text="Passwords match" />
          </div>
        )}

        <button type="submit" className="auth-submit" disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="auth-footer-text">
        Already have an account?{" "}
        <button type="button" className="auth-link" onClick={onSwitchToLogin}>
          Log in
        </button>
      </p>
    </>
  );
}

function ChecklistItem({ ok, text }) {
  return (
    <span className={`auth-checklist-item ${ok ? "ok" : ""}`}>
      <span className="auth-checklist-dot" />
      {text}
    </span>
  );
}
