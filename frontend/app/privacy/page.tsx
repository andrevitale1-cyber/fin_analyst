export default function Privacy() {
  return (
    <div className="max-w-4xl mx-auto p-8 text-gray-300 font-sans">
      <h1 className="text-3xl font-bold text-white mb-6">Política de Privacidade</h1>
      
      <h2 className="text-xl font-bold text-white mt-6 mb-2">1. Coleta de Dados</h2>
      <p>Coletamos apenas seu e-mail e nome para autenticação via Clerk e processamento de pagamentos via Stripe.</p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">2. Uso das Informações</h2>
      <p>Seus dados são usados exclusivamente para fornecer o serviço contratado. Não vendemos suas informações para terceiros.</p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">3. Segurança</h2>
      <p>Utilizamos criptografia de ponta a ponta e provedores seguros (Google Cloud, Vercel, Clerk).</p>
    </div>
  );
}