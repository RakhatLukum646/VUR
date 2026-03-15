import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function SignupPage() {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSignup = (e: React.FormEvent) => {
    e.preventDefault();

    // Temporary demo signup
    localStorage.setItem(
      'mockUser',
      JSON.stringify({ name, email })
    );

    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        <h1 className="text-xl font-bold text-gray-900 mb-6">
          Create Account
        </h1>

        <form onSubmit={handleSignup} className="space-y-5">
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e)=>setName(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
          />

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e)=>setEmail(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e)=>setPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900"
          />

          <button
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Sign Up
          </button>
        </form>
      </div>
    </div>
  );
}