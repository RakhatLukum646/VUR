import { useState } from "react";
import { loginUser } from "../../services/authApi";
import { useAuthStore } from "../../store/useAuthStore";

export default function LoginForm() {
  const { login } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await loginUser({ email, password });
      login(result.user, result.access_token);
      window.location.href = "/profile";
    } catch {
      setError("Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-lg"
    >
      <h2 className="mb-6 text-2xl font-semibold text-white">Sign In</h2>

      <div className="mb-4">
        <label className="mb-2 block text-sm text-slate-300">Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-white outline-none focus:border-cyan-400"
          placeholder="Enter your email"
        />
      </div>

      <div className="mb-4">
        <label className="mb-2 block text-sm text-slate-300">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-xl border border-slate-600 bg-slate-800 px-4 py-3 text-white outline-none focus:border-cyan-400"
          placeholder="Enter your password"
        />
      </div>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-cyan-500 px-4 py-3 font-medium text-black transition hover:bg-cyan-400 disabled:opacity-60"
      >
        {loading ? "Signing in..." : "Sign In"}
      </button>
    </form>
  );
}