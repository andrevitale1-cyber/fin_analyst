import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Define quais rotas são PROTEGIDAS (precisa de login)
// O resto (como a home "/") será público por padrão
const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/profile(.*)',
]);

export default clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Pula arquivos internos do Next.js e estáticos
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Sempre roda para rotas de API
    '/(api|trpc)(.*)',
  ],
};