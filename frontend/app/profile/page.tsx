"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Settings, User, Mail, Lock, CreditCard, Save, ChevronLeft, Loader2, LogOut } from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  
  // Estados para armazenar os dados
  const [user, setUser] = useState<any>(null);
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  
  const [novaSenha, setNovaSenha] = useState("");
  
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [loadingPassword, setLoadingPassword] = useState(false);
  const [msg, setMsg] = useState({ text: "", type: "" }); // type: 'success' or 'error'

  // Carrega dados do LocalStorage ao abrir
  useEffect(() => {
    const storedUser = localStorage.getItem('usuario');
    if (storedUser) {
      const parsedUser = JSON.parse(storedUser);
      setUser(parsedUser);
      setNome(parsedUser.nome || "");
      setEmail(parsedUser.email || "");
    } else {
      router.push('/login');
    }
  }, [router]);

  // Função para salvar dados pessoais
  const handleUpdateProfile = async () => {
    setLoadingProfile(true);
    setMsg({ text: "", type: "" });

    try {
      const res = await fetch('https://api-finanalyzer.onrender.com/api/update-profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, nome, email })
      });
      
      const data = await res.json();

      if (res.ok) {
        // Atualiza o LocalStorage com os novos dados
        localStorage.setItem('usuario', JSON.stringify(data.usuario));
        setUser(data.usuario);
        setMsg({ text: "Dados atualizados com sucesso!", type: "success" });
      } else {
        setMsg({ text: "Erro ao atualizar.", type: "error" });
      }
    } catch (error) {
      setMsg({ text: "Erro de conexão.", type: "error" });
    } finally {
      setLoadingProfile(false);
    }
  };

  // Função para trocar senha
  const handleUpdatePassword = async () => {
    if (!novaSenha) return;
    setLoadingPassword(true);
    
    try {
      const res = await fetch('https://api-finanalyzer.onrender.com/api/update-password', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: user.id, nova_senha: novaSenha })
      });

      if (res.ok) {
        setMsg({ text: "Senha alterada com sucesso!", type: "success" });
        setNovaSenha("");
      } else {
        setMsg({ text: "Erro ao alterar senha.", type: "error" });
      }
    } catch (error) {
      setMsg({ text: "Erro de conexão.", type: "error" });
    } finally {
      setLoadingPassword(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('usuario');
    router.push('/login');
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-[#0E1117] p-6 font-sans text-gray-100">
      
      {/* Header com botão voltar */}
      <div className="max-w-4xl mx-auto mb-8 flex justify-between items-center">
        <Link href="/dashboard" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
          <ChevronLeft size={20} />
          <span>Voltar para Dashboard</span>
        </Link>
        <button onClick={handleLogout} className="flex items-center gap-2 text-red-400 hover:text-red-300 transition-colors text-sm">
          <LogOut size={16} /> Sair da conta
        </button>
      </div>

      <div className="max-w-4xl mx-auto">
        
        {/* Título da Página */}
        <div className="flex items-center gap-4 mb-8">
          <div className="p-3 bg-[#161b22] rounded-xl border border-gray-800">
            <Settings className="text-blue-500 w-8 h-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Sua Conta</h1>
            <p className="text-gray-400">Administre seus detalhes pessoais e assinatura.</p>
          </div>
        </div>

        {/* Mensagens de Sucesso/Erro */}
        {msg.text && (
          <div className={`mb-6 p-4 rounded-lg border ${msg.type === 'success' ? 'bg-green-900/20 border-green-800 text-green-400' : 'bg-red-900/20 border-red-800 text-red-400'}`}>
            {msg.text}
          </div>
        )}

        {/* SEÇÃO 1: Identificação */}
        <section className="bg-[#161b22] border border-gray-800 rounded-2xl p-6 mb-6">
          <h2 className="text-xl font-semibold mb-1">Identificação</h2>
          <p className="text-sm text-gray-500 mb-6">Altere suas informações pessoais básicas.</p>

          <div className="grid gap-6 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Nome Completo</label>
              <div className="relative">
                <User className="absolute left-3 top-3 text-gray-600" size={18} />
                <input 
                  type="text" 
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  className="w-full bg-[#0d1117] border border-gray-700 text-white pl-10 pr-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500 transition-all"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 text-gray-600" size={18} />
                <input 
                  type="email" 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-[#0d1117] border border-gray-700 text-white pl-10 pr-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500 transition-all"
                />
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-end">
            <button 
              onClick={handleUpdateProfile}
              disabled={loadingProfile}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {loadingProfile ? <Loader2 className="animate-spin" size={18}/> : <Save size={18} />}
              Salvar Alterações
            </button>
          </div>
        </section>

        {/* SEÇÃO 2: Senha */}
        <section className="bg-[#161b22] border border-gray-800 rounded-2xl p-6 mb-6">
          <h2 className="text-xl font-semibold mb-1">Senha</h2>
          <p className="text-sm text-gray-500 mb-6">Defina uma nova senha para acessar sua conta.</p>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Nova Senha</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-gray-600" size={18} />
              <input 
                type="password" 
                placeholder="********"
                value={novaSenha}
                onChange={(e) => setNovaSenha(e.target.value)}
                className="w-full bg-[#0d1117] border border-gray-700 text-white pl-10 pr-4 py-2.5 rounded-lg focus:outline-none focus:border-blue-500 transition-all"
              />
            </div>
          </div>

          <div className="mt-6">
            <button 
              onClick={handleUpdatePassword}
              disabled={loadingPassword || !novaSenha}
              className="bg-[#21262d] hover:bg-[#30363d] text-white border border-gray-700 px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {loadingPassword ? <Loader2 className="animate-spin" size={18}/> : "Definir nova senha"}
            </button>
          </div>
        </section>

        {/* SEÇÃO 3: Premium */}
        <section className="bg-gradient-to-r from-[#161b22] to-[#0d1117] border border-blue-900/30 rounded-2xl p-6 relative overflow-hidden">
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-xl font-semibold text-white">Assinatura Premium</h2>
              <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${user.plano === 'premium' ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-300'}`}>
                {user.plano === 'premium' ? 'ATIVO' : 'FREE'}
              </span>
            </div>
            <p className="text-sm text-gray-400 mb-6 max-w-lg">
              {user.plano === 'premium' 
                ? "Você tem acesso total a todas as funcionalidades de IA e análises ilimitadas."
                : "Faça o upgrade para desbloquear análises ilimitadas e relatórios avançados."}
            </p>

            <button className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2.5 rounded-lg font-bold shadow-lg shadow-blue-900/20 transition-all flex items-center gap-2">
              <CreditCard size={18} />
              {user.plano === 'premium' ? "Gerenciar Assinatura" : "Virar Premium"}
            </button>
          </div>
          
          {/* Efeito de fundo */}
          <div className="absolute right-0 top-0 h-full w-1/3 bg-blue-600/5 blur-[80px] pointer-events-none"></div>
        </section>

      </div>
    </div>
  );
}