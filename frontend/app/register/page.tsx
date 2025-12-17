'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { UserPlus } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({ nome: '', email: '', senha: '' });
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      const res = await fetch('http://localhost:8000/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) throw new Error(data.error || 'Erro ao cadastrar');

      alert('Conta criada com sucesso!');
      router.push('/login'); 
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0E1117] text-white">
      <form onSubmit={handleSubmit} className="bg-[#161b22] p-8 rounded-2xl shadow-2xl border border-gray-800 w-96 animate-in fade-in zoom-in duration-500">
        <div className="flex justify-center mb-6">
          <div className="bg-green-600 p-3 rounded-xl shadow-lg shadow-green-900/20">
            <UserPlus size={32} className="text-white" />
          </div>
        </div>
        
        <h2 className="text-2xl font-bold mb-2 text-center">Criar Nova Conta</h2>
        <p className="text-gray-400 text-sm text-center mb-8">Comece a analisar empresas com IA.</p>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg mb-6 text-sm text-center">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Nome</label>
            <input
              name="nome"
              type="text"
              placeholder="Seu Nome"
              className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-green-500/50 outline-none transition-all"
              onChange={handleChange}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Email</label>
            <input
              name="email"
              type="email"
              placeholder="seu@email.com"
              className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-green-500/50 outline-none transition-all"
              onChange={handleChange}
              required
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Senha</label>
            <input
              name="senha"
              type="password"
              placeholder="••••••"
              className="w-full bg-[#0d1117] border border-gray-700 rounded-lg px-4 py-3 text-white focus:ring-2 focus:ring-green-500/50 outline-none transition-all"
              onChange={handleChange}
              required
            />
          </div>
        </div>

        <button type="submit" className="w-full mt-8 bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-green-900/20">
          Cadastrar
        </button>

        <p className="mt-6 text-center text-sm text-gray-500">
          Já tem conta? <a href="/login" className="text-blue-400 hover:text-blue-300 font-medium transition-colors">Faça login</a>
        </p>
      </form>
    </div>
  );
}