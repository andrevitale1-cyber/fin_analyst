"use client";
import { UserProfile } from "@clerk/nextjs";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export default function ProfilePage() {
  return (
    <div className="min-h-screen bg-[#0E1117] py-10 px-4 flex flex-col items-center">
      
      {/* Botão de Voltar */}
      <div className="w-full max-w-[880px] mb-6">
        <Link 
          href="/dashboard" 
          className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors py-2 px-3 rounded-lg hover:bg-white/5"
        >
           <ChevronLeft size={20} />
           <span className="font-medium">Voltar para Dashboard</span>
        </Link>
      </div>

      {/* Componente Completo do Clerk */}
      <UserProfile 
        appearance={{
          elements: {
            rootBox: "w-full max-w-4xl",
            card: "bg-[#161b22] border border-gray-800 shadow-xl",
            navbar: "hidden md:flex border-r border-gray-800",
            navbarButton: "text-gray-400 hover:text-white hover:bg-white/5",
            headerTitle: "text-white",
            headerSubtitle: "text-gray-400",
            profileSectionTitleText: "text-white",
            userPreviewMainIdentifier: "text-white",
            userPreviewSecondaryIdentifier: "text-gray-400"
          }
        }}
      />
    </div>
  );
}