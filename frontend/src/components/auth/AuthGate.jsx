import { useEffect, useState } from "react";
import App from "../../App";
import { clearSession, fetchMe, getStoredUser, getToken, setSession } from "../../api/authClient";
import AuthLayout from "./AuthLayout";
import LoginPage from "./LoginPage";
import RegisterPage from "./RegisterPage";
import VerifyOtpPage from "./VerifyOtpPage";

export default function AuthGate() {
  const [user, setUser] = useState(() => (getToken() ? getStoredUser() : null));
  const [checkingSession, setCheckingSession] = useState(() => Boolean(getToken()));
  const [view, setView] = useState("login");
  const [pendingEmail, setPendingEmail] = useState("");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setCheckingSession(false);
      return;
    }
    fetchMe(token)
      .then((freshUser) => {
        setSession(token, freshUser);
        setUser(freshUser);
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setCheckingSession(false));
  }, []);

  const handleLoggedIn = (token, loggedInUser) => {
    setSession(token, loggedInUser);
    setUser(loggedInUser);
  };

  const handleLogout = () => {
    clearSession();
    setUser(null);
    setView("login");
  };

  if (checkingSession) {
    return null;
  }

  if (user) {
    return (
      <>
        <div className="auth-session-bar">
          <span>
            Signed in as <span className="auth-session-user">{user.username}</span>
          </span>
          <button type="button" className="auth-logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
        <App />
      </>
    );
  }

  return (
    <AuthLayout>
      {view === "login" && (
        <LoginPage
          onLoggedIn={handleLoggedIn}
          onSwitchToRegister={() => setView("register")}
          onNeedsVerification={(emailOrUsername) => {
            setPendingEmail(emailOrUsername);
            setView("verify-otp");
          }}
        />
      )}

      {view === "register" && (
        <RegisterPage
          onRegistered={(email) => {
            setPendingEmail(email);
            setView("verify-otp");
          }}
          onSwitchToLogin={() => setView("login")}
        />
      )}

      {view === "verify-otp" && (
        <VerifyOtpPage
          email={pendingEmail}
          onVerified={() => setView("login")}
          onSwitchToLogin={() => setView("login")}
        />
      )}
    </AuthLayout>
  );
}
