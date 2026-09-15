import { useState } from "react";
import { IconFileText, IconAlert } from "./Icons";

export default function LoginForm({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await onLogin(email, password);
    } catch (err) {
      setError(err.message || "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="card login-card" onSubmit={handleSubmit}>
        <div className="login-brand">
          <div className="brand-mark" style={{ width: 44, height: 44, borderRadius: 12 }}>
            <IconFileText width={22} height={22} />
          </div>
          <div>
            <h2>Contract Review</h2>
            <p className="muted" style={{ margin: "4px 0 0" }}>
              Sign in with your procurement team account.
            </p>
          </div>
        </div>

        <label className="field-label" htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoFocus
        />

        <label className="field-label" htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && (
          <div className="error-text">
            <IconAlert width={14} height={14} />
            {error}
          </div>
        )}

        <button type="submit" disabled={busy}>
          {busy ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
