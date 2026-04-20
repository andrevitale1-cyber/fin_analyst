import { useLocale } from 'next-intl';

export default function Privacy() {
  const locale = useLocale();
  return (
    <div className="max-w-4xl mx-auto p-8 text-gray-300 font-sans">
      <h1 className="text-3xl font-bold text-white mb-6">
        {locale === 'en' ? 'Privacy Policy' : 'Política de Privacidade'}
      </h1>
      
      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '1. Data Collection' : '1. Coleta de Dados'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'We only collect your email and name for authentication via Clerk and payment processing via Stripe.' 
          : 'Coletamos apenas seu e-mail e nome para autenticação via Clerk e processamento de pagamentos via Stripe.'}
      </p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '2. Use of Information' : '2. Uso das Informações'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'Your data is strictly used to provide the contracted service. We do not sell your information to third parties.' 
          : 'Seus dados são usados exclusivamente para fornecer o serviço contratado. Não vendemos suas informações para terceiros.'}
      </p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '3. Security' : '3. Segurança'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'We use end-to-end encryption and secure providers (Google Cloud, Vercel, Clerk).' 
          : 'Utilizamos criptografia de ponta a ponta e provedores seguros (Google Cloud, Vercel, Clerk).'}
      </p>
    </div>
  );
}