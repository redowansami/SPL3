import { useEffect, useRef, useState } from "react";
import { resendOtp, verifyOtp } from "../../api/authClient";

const RESEND_COOLDOWN_SECONDS = 30;

export default function VerifyOtpPage({ email, onVerified, onSwitchToLogin }) {
  const [otpCode, setOtpCode] = useState("");
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const cooldownTimer = useRef(null);

  useEffect(() => () => clearInterval(cooldownTimer.current), []);

  const startCooldown = () => {
    setCooldown(RESEND_COOLDOWN_SECONDS);
    cooldownTimer.current = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(cooldownTimer.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setInfo(null);

    if (otpCode.length !== 6) {
      setError("Enter the 6-digit code from your email.");
      return;
    }

    setSubmitting(true);
    try {
      await verifyOtp({ email, otpCode });
      onVerified();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleResend = async () => {
    setError(null);
    setInfo(null);
    try {
      await resendOtp({ email });
      setInfo("A new code has been sent to your email.");
      startCooldown();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <>
      <h1 className="auth-title">Verify your email</h1>
      <p className="auth-subtitle">
        We sent a 6-digit code to <span className="auth-otp-email">{email}</span>. Enter it below to
        confirm your account.
      </p>

      {error && <div className="auth-alert auth-alert-error">{error}</div>}
      {info && <div className="auth-alert auth-alert-success">{info}</div>}

      <form className="auth-form" onSubmit={handleSubmit}>
        <input
          className="auth-otp-input"
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          placeholder="------"
          value={otpCode}
          autoFocus
          onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
        />

        <button type="submit" className="auth-submit" disabled={submitting || otpCode.length !== 6}>
          {submitting ? "Verifying…" : "Verify email"}
        </button>

        <button
          type="button"
          className="auth-secondary-btn"
          onClick={handleResend}
          disabled={cooldown > 0}
        >
          {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend code"}
        </button>
      </form>

      <p className="auth-footer-text">
        Already verified?{" "}
        <button type="button" className="auth-link" onClick={onSwitchToLogin}>
          Go to login
        </button>
      </p>
    </>
  );
}
