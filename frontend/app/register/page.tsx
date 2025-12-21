'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link'; // Recomendado para navegação interna no Next.js
import { Eye, EyeOff, Check, X } from 'lucide-react'; // Ícones para feedback visual

export default function Register() {
  const router = useRouter();
  
  // Estados do formulário
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });
  
  // Estados de controle de UI
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false); // Mostrar/Ocultar senha
  const [touchedPassword, setTouchedPassword] = useState(false); // Só mostra regras se usuário digitou algo

  const API_URL = "https://api-finanalyzer.onrender.com";

  // --- REGRAS DE VALIDAÇÃO (Espelho do Backend) ---
  const requirements = [
    { label: "Mínimo 8 caracteres", test: (v: string) => v.length >= 8 },
    { label: "Máximo 72 caracteres", test: (v: string) => v.length <= 72 }, // Proteção contra crash do Bcrypt
    { label: "Letra maiúscula", test: (v: string) => /[A-Z]/.test(v) },
    { label: "Letra minúscula", test: (v: string) => /[a-z]/.test(v) },
    { label: "Número", test: (v: string) => /[0-9]/.test(v) },
    { label: "Caractere especial (!@#$)", test: (v: string) => /[\W_]/.test(v) },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log(`Enviando dados para: ${API_URL}/auth/register`);
      
      const res = await fetch(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome: formData.name, 
          email: formData.email,
          senha: formData.password 
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        // Tenta pegar a mensagem de erro específica do Pydantic (Backend)
        if (data.detail && Array.isArray(data.detail)) {
            // Remove o prefixo técnico "Value error, " se existir
            throw new Error(data.detail[0].msg.replace('Value error, ', ''));
        }
        throw new Error(data.detail || 'Erro ao criar conta');
      }

      alert('Conta criada com sucesso! Faça login.');
      router.push('/login'); 
    } catch (err: any) {
      console.error("Erro no registro:", err);
      setError(err.message || "Erro de conexão com o servidor.");
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
          {/* Campo Nome */}
          <div>
            <label className="block text-sm font-medium mb-1">Nome</label>
            <input
              type="text"
              className="w-full p-2 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none transition-colors"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          {/* Campo Email */}
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

          {/* Campo Senha com Validação Visual */}
          <div>
            <label className="block text-sm font-medium mb-1">Senha</label>
            <div className="relative">
                <input
                    type={showPassword ? "text" : "password"}
                    maxLength={72} // <--- Proteção Importante
                    className="w-full p-2 pr-10 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none transition-colors"
                    value={formData.password}
                    onChange={(e) => {
                        setFormData({ ...formData, password: e.target.value });
                        setTouchedPassword(true);
                    }}
                    required
                />
                {/* Botão Olho */}
                <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-2.5 text-gray-400 hover:text-white transition-colors"
                >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
            </div>

            {/* Checklist de Requisitos (Só aparece se o usuário começou a digitar) */}
            {touchedPassword && (
                <div className="mt-3 p-3 bg-gray-800/50 rounded text-xs space-y-1 border border-gray-700">
                    <p className="font-semibold text-gray-400 mb-2">Sua senha deve ter:</p>
                    {requirements.map((req, idx) => {
                        const isValid = req.test(formData.password);
                        return (
                            <div 
                                key={idx} 
                                className={`flex items-center space-x-2 ${isValid ? "text-green-400" : "text-gray-500"}`}
                            >
                                {isValid ? <Check size={14} /> : <div className="w-3.5 h-3.5 rounded-full border border-gray-600" />}
                                <span>{req.label}</span>
                            </div>
                        );
                    })}
                </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 rounded font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Criando conta...' : 'Cadastrar'}
          </button>
        </form>

        <div className="mt-4 text-center text-sm">
          <p className="text-gray-400">
            Já tem conta?{' '}
            <Link href="/login" className="text-blue-400 hover:underline">
              Faça login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}