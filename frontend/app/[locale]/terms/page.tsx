import { useLocale } from 'next-intl';

export default function Terms() {
  const locale = useLocale();
  return (
    <div className="max-w-4xl mx-auto p-8 text-gray-300 font-sans">
      <h1 className="text-3xl font-bold text-white mb-6">
        {locale === 'en' ? 'Terms of Use' : 'Termos de Uso'}
      </h1>
      <p className="mb-4">
        {locale === 'en' ? 'Last updated: January 29, 2026' : 'Última atualização: 29 de Janeiro de 2026'}
      </p>
      
      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '1. Acceptance' : '1. Aceitação'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'By accessing FinAnalyzer.AI, you agree to these terms of service.' 
          : 'Ao acessar o FinAnalyzer.AI, você concorda com estes termos de serviço.'}
      </p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '2. Services' : '2. Serviços'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'We provide automated financial analyses via AI. The service is an auxiliary tool and does not constitute investment advice.' 
          : 'Fornecemos análises financeiras automatizadas via IA. O serviço é uma ferramenta auxiliar e não constitui recomendação de investimento.'}
      </p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '3. Subscriptions' : '3. Assinaturas'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'The Premium plan is billed monthly. You can cancel anytime before renewal.' 
          : 'O plano Premium é cobrado mensalmente. Você pode cancelar a qualquer momento antes da renovação.'}
      </p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '4. Liability' : '4. Responsabilidade'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'We are not responsible for financial decisions made based on our analyses. Past performance is no guarantee of future results.' 
          : 'Não nos responsabilizamos por decisões financeiras tomadas com base em nossas análises. Rentabilidade passada não garante futuro.'}
      </p>
    </div>
  );
}