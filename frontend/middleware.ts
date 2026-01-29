import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Define as rotas que exigem login
const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/profile(.*)',
]);

export default clerkMiddleware((auth, req) => {
  // Na versão 5, o auth().protect() é síncrono e direto
  if (isProtectedRoute(req)) {
    auth().protect();
  }
});

export const config = {
  matcher: [
    // Pula arquivos estáticos
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Sempre roda na API
    '/(api|trpc)(.*)',
  ],
};