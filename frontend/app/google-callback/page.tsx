"use client";
import { useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const dataString = searchParams.get('data');
    
    if (dataString) {
      try {
        // 1. Pega os dados que vieram do backend
        const userData = JSON.parse(dataString);
        
        // 2. Salva no navegador (igual ao login normal)
        localStorage.setItem('usuario', JSON.stringify(userData));
        
        // 3. Manda pro Dashboard
        router.push('/dashboard');
      } catch (e) {
        console.error("Erro ao processar login Google:", e);
        router.push('/login?error=google_fail');
      }
    } else {
      router.push('/login');
    }
  }, [router, searchParams]);

  return (
    <div className="min-h-screen bg-[#0E1117] flex flex-col items-center justify-center text-white">
      <Loader2 className="w-10 h-10 animate-spin text-blue-500 mb-4" />
      <p className="text-gray-400">Autenticando com Google...</p>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#0E1117]" />}>
      <CallbackContent />
    </Suspense>
  );
}