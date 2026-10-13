const API_BASE = "http://localhost:8000";

const TOKEN_KEY = "atlas_token";
const USER_KEY = "atlas_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function parseJsonOrThrow(res, fallbackMessage) {
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || fallbackMessage);
  }
  return data;
}

export async function register({ username, email, password, confirmPassword }) {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      email,
      password,
      confirm_password: confirmPassword,
    }),
  });
  return parseJsonOrThrow(res, `Registration failed (${res.status})`);
}

export async function verifyOtp({ email, otpCode }) {
  const res = await fetch(`${API_BASE}/api/auth/verify-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, otp_code: otpCode }),
  });
  return parseJsonOrThrow(res, `Verification failed (${res.status})`);
}

export async function resendOtp({ email }) {
  const res = await fetch(`${API_BASE}/api/auth/resend-otp`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return parseJsonOrThrow(res, `Could not resend code (${res.status})`);
}

export async function login({ usernameOrEmail, password }) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
  });
  return parseJsonOrThrow(res, `Login failed (${res.status})`);
}

export async function fetchMe(token) {
  const res = await fetch(`${API_BASE}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return parseJsonOrThrow(res, `Could not load profile (${res.status})`);
}
