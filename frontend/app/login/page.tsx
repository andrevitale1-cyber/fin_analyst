import { SignIn } from "@clerk/nextjs";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export default function Page() {
  return (
    <div className="min-h-screen bg-[#0E1117] flex flex-col items-center justify-center relative">
      
      {/* Botão Flutuante para voltar à Landing Page */}
      <Link 
        href="/" 
        className="absolute top-8 left-8 text-gray-400 hover:text-white flex items-center gap-2 transition-colors py-2 px-4 rounded-lg hover:bg-white/5 font-medium"
      >
        <ChevronLeft size={20} />
        Voltar para Início
      </Link>

      {/* Componente de Login */}
      <SignIn redirectUrl="/dashboard" />
    </div>
  );
}