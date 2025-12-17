'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Register() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // URL FIXA para garantir a conexão (Depurar erro de variável)
  const API_URL = "https://api-finanalyzer.onrender.com"; 

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Log para você ver no navegador (F12)
      console.log(`Tentando registrar em: ${API_URL}/auth/register`);

      const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Erro ao registrar');
      }

      alert('Conta criada com sucesso!');
      router.push('/login'); 
    } catch (err: any) {
      console.error("Erro completo:", err);
      setError("Erro de conexão: O Backend pode estar 'dormindo' (Render Free). Tente de novo em 30 segundos.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-black text-white">
      <div className="w-full max-w-md p-8 bg-gray-900 rounded-lg border border-gray-800">
        <h1 className="text-2xl font-bold mb-6 text-center">Criar Nova Conta</h1>
        
        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-500 rounded text-red-200 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Nome</label>
            <input
              type="text"
              className="w-full p-2 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              className="w-full p-2 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Senha</label>
            <input
              type="password"
              className="w-full p-2 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded font-bold transition-colors disabled:opacity-50"
          >
            {loading ? 'Carregando...' : 'Cadastrar'}
          </button>
        </form>
        <div className="mt-4 text-center text-sm">
          <p className="text-gray-400">Já tem conta? <a href="/login" className="text-blue-400 hover:underline">Faca login</a></p>
        </div>
      </div>
    </div>
  );
}