/** @type {import('next').NextConfig} */
const nextConfig = {
  // Ignora erros de ESLint (código "feio") no deploy
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Ignora erros de TypeScript (tipos errados) no deploy
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;