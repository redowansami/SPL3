import { useState } from "react";
import { login } from "../../api/authClient";
import PasswordField from "./PasswordField";

export default function LoginPage({ onLoggedIn, onSwitchToRegister, onNeedsVerification }) {
  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!usernameOrEmail.trim() || !password) {
      setError("Enter your username/email and password.");
      return;
    }

    setSubmitting(true);
    try {
      const data = await login({ usernameOrEmail, password });
      onLoggedIn(data.access_token, data.user);
    } catch (err) {
      if (err.message.toLowerCase().includes("not verified") && usernameOrEmail.includes("@")) {
        onNeedsVerification(usernameOrEmail);
        return;
      }
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <h1 className="auth-title">Welcome back</h1>
      <p className="auth-subtitle">Log in to continue to ATLAS-Scan.</p>

      {error && <div className="auth-alert auth-alert-error">{error}</div>}

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="auth-field">
          <label className="auth-label" htmlFor="login-identifier">
            Username or email
          </label>
          <input
            id="login-identifier"
            className="auth-input"
            type="text"
            placeholder="yourname or you@example.com"
            value={usernameOrEmail}
            autoComplete="username"
            onChange={(e) => setUsernameOrEmail(e.target.value)}
            required
          />
        </div>

        <PasswordField
          id="login-password"
          label="Password"
          placeholder="Your password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
        />

        <button type="submit" className="auth-submit" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="auth-footer-text">
        Don&apos;t have an account?{" "}
        <button type="button" className="auth-link" onClick={onSwitchToRegister}>
          Register
        </button>
      </p>
    </>
  );
}
