'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link'; // Importante para navegação interna otimizada

export default function Login() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const API_URL = "https://api-finanalyzer.onrender.com";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: formData.email,
            senha: formData.password 
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        // Se for erro de validação (422) ou login (401)
        const errorMessage = data.detail || 'Email ou senha incorretos';
        // Se o erro for uma lista (comum no FastAPI/Pydantic), pegamos o primeiro msg
        if (Array.isArray(errorMessage)) {
             throw new Error(errorMessage[0].msg);
        }
        throw new Error(errorMessage);
      }

      // Salva o usuário no navegador para manter logado
      localStorage.setItem('usuario', JSON.stringify(data.usuario));
      
      // Opcional: Toast ou feedback visual aqui
      router.push('/'); 
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-black text-white">
      <div className="w-full max-w-md p-8 bg-gray-900 rounded-lg border border-gray-800">
        <h1 className="text-2xl font-bold mb-6 text-center">Login</h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              className="w-full p-2 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none transition-colors"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Senha</label>
            <input
              type="password"
              // AQUI ESTÁ A PROTEÇÃO CONTRA O ERRO "72 BYTES"
              maxLength={72} 
              className="w-full p-2 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none transition-colors"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        <div className="mt-4 text-center text-sm">
          <p className="text-gray-400">
            Não tem conta?{' '}
            <Link href="/register" className="text-blue-400 hover:underline">
              Cadastre-se
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}