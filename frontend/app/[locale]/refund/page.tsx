import { useLocale } from 'next-intl';

export default function Refund() {
  const locale = useLocale();
  return (
    <div className="max-w-4xl mx-auto p-8 text-gray-300 font-sans">
      <h1 className="text-3xl font-bold text-white mb-6">
        {locale === 'en' ? 'Refund Policy' : 'Política de Reembolso'}
      </h1>
      
      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '1. Guarantee' : '1. Garantia'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'We offer a full refund if requested within 7 days after the first purchase, in case the service does not meet your expectations.' 
          : 'Oferecemos reembolso integral se solicitado em até 7 dias após a primeira compra, caso o serviço não atenda às expectativas.'}
      </p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '2. How to Request' : '2. Como Solicitar'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'Send an email to suportefinanalyzerai@gmail.com with your payment receipt.' 
          : 'Envie um email para suportefinanalyzerai@gmail.com com o comprovante de pagamento.'}
      </p>

      <h2 className="text-xl font-bold text-white mt-6 mb-2">
        {locale === 'en' ? '3. Cancellation' : '3. Cancelamento'}
      </h2>
      <p>
        {locale === 'en' 
          ? 'Canceling your subscription stops future charges, but does not refund periods already used outside the 7-day guarantee.' 
          : 'O cancelamento da assinatura interrompe cobranças futuras, mas não reembolsa períodos já utilizados fora do prazo de garantia de 7 dias.'}
      </p>
    </div>
  );
}