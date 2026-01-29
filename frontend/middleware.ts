import { clerkMiddleware } from "@clerk/nextjs/server";

// Middleware simples: apenas carrega o contexto do Clerk, sem forçar bloqueios
export default clerkMiddleware();

export const config = {
  matcher: [
    // Pula arquivos estáticos (_next, imagens, etc)
    '/((?!.*\\..*|_next).*)', 
    '/', 
    '/(api|trpc)(.*)'
  ],
};