"use client";
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { BarChart3, Loader2, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch('https://api-finanalyzer.onrender.com/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, senha: password })
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem('usuario', JSON.stringify(data.usuario));
        router.push('/dashboard');
      } else {
        setError(data.detail || "Email ou senha incorretos.");
      }
    } catch (err) {
      setError("Erro de conexão com o servidor.");
    } finally {
      setLoading(false);
    }
  };

  // --- FUNÇÃO QUE FALTAVA ---
  const handleGoogleLogin = () => {
    // Redireciona para a rota do backend que inicia o login com Google
    window.location.href = "https://api-finanalyzer.onrender.com/auth/google/login";
  };

  return (
    <div className="min-h-screen bg-[#0E1117] flex flex-col items-center justify-center p-4 font-sans">
      
      <div className="mb-8 text-center animate-in fade-in slide-in-from-bottom-4 duration-700">
        <Link href="/" className="inline-flex items-center gap-2 mb-2 group">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/20 group-hover:scale-110 transition-transform">
            <BarChart3 className="text-white w-6 h-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight text-white">
            FinAnalyzer <span className="text-blue-500">.AI</span>
          </span>
        </Link>
      </div>

      <div className="w-full max-w-md bg-[#161b22] border border-gray-800 rounded-2xl shadow-2xl p-8 animate-in zoom-in-95 duration-500">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Faça Login</h1>
          <p className="text-gray-400 text-sm">...na plataforma de IA mais completa para investidores!</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <input 
              type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#0d1117] border border-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-gray-600"
              required
            />
          </div>
          <div>
            <input 
              type="password" placeholder="Senha" value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#0d1117] border border-gray-700 text-white px-4 py-3 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-gray-600"
              required
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="text-red-400 text-xs font-medium min-h-[20px] flex items-center gap-1 max-w-[200px] leading-tight">
              {error && <><AlertCircle size={12} className="shrink-0" /> {error}</>}
            </div>
            <a href="#" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">Esqueceu sua senha?</a>
          </div>

          <button type="submit" disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-blue-900/20 transition-all active:scale-[0.98] flex items-center justify-center gap-2">
            {loading ? <Loader2 className="animate-spin" size={20} /> : "Logar"}
          </button>
        </form>

        <div className="relative my-8">
          <div className="absolute inset-0 flex items-center"><span className="w-full border-t border-gray-700"></span></div>
          <div className="relative flex justify-center text-xs uppercase"><span className="bg-[#161b22] px-2 text-gray-500 font-medium">OU</span></div>
        </div>

        {/* --- BOTÃO CORRIGIDO COM ONCLICK --- */}
        <button 
          type="button" 
          onClick={handleGoogleLogin} 
          className="w-full bg-white hover:bg-gray-100 text-gray-900 font-bold py-3 rounded-lg border border-gray-200 transition-all flex items-center justify-center gap-3"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" /><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" /><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.26z" fill="#FBBC05" /><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" /></svg>
          Logar com o Google
        </button>

        <div className="mt-8 text-center border-t border-gray-800 pt-6">
          <p className="text-gray-500 text-sm">Ainda não tem uma conta? <Link href="/register" className="text-blue-400 font-bold hover:text-blue-300 transition-colors">Cadastre-se!</Link></p>
        </div>
      </div>
    </div>
  );
}