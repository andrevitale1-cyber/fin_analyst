"use client";
import { useLocale } from 'next-intl';
import Link from 'next/link';
import { BarChart3, ArrowLeft, RefreshCw, Clock, CheckCircle, XCircle, Mail, HelpCircle } from 'lucide-react';

export default function Refund() {
  const locale = useLocale();
  const en = locale === 'en';

  return (
    <div className="min-h-screen bg-[#0A0D14] text-gray-300 font-sans">
      {/* Navbar */}
      <nav className="border-b border-white/10 bg-[#0A0D14]/80 backdrop-blur-xl sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg">
              <BarChart3 className="text-white w-5 h-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              FinAnalyzer <span className="text-blue-500">.AI</span>
            </span>
          </Link>
          <Link href="/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
            <ArrowLeft size={16} />
            {en ? 'Back' : 'Voltar'}
          </Link>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-purple-500/10 border border-purple-500/20 rounded-2xl flex items-center justify-center">
              <RefreshCw className="text-purple-400 w-6 h-6" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
            {en ? 'Refund Policy' : 'Política de Reembolso'}
          </h1>
          <p className="text-gray-500 text-sm">
            {en ? 'Last updated: April 24, 2026' : 'Última atualização: 24 de Abril de 2026'}
          </p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
          <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-5 text-center">
            <CheckCircle className="text-emerald-400 w-7 h-7 mx-auto mb-3" />
            <p className="text-white font-bold text-lg mb-1">{en ? '7-Day Guarantee' : 'Garantia de 7 Dias'}</p>
            <p className="text-gray-400 text-xs leading-relaxed">{en ? 'Full refund within 7 days of first payment' : 'Reembolso integral em até 7 dias do primeiro pagamento'}</p>
          </div>
          <div className="bg-blue-500/5 border border-blue-500/20 rounded-2xl p-5 text-center">
            <Clock className="text-blue-400 w-7 h-7 mx-auto mb-3" />
            <p className="text-white font-bold text-lg mb-1">{en ? '3 Business Days' : '3 Dias Úteis'}</p>
            <p className="text-gray-400 text-xs leading-relaxed">{en ? 'Average processing time for approved refunds' : 'Prazo médio de processamento de reembolsos aprovados'}</p>
          </div>
          <div className="bg-purple-500/5 border border-purple-500/20 rounded-2xl p-5 text-center">
            <Mail className="text-purple-400 w-7 h-7 mx-auto mb-3" />
            <p className="text-white font-bold text-lg mb-1">{en ? 'Simple Process' : 'Processo Simples'}</p>
            <p className="text-gray-400 text-xs leading-relaxed">{en ? 'Just send an email — no complicated forms' : 'Basta enviar um e-mail — sem formulários complicados'}</p>
          </div>
        </div>

        <div className="space-y-10">

          <Section icon={<CheckCircle size={18} className="text-emerald-400" />} title={en ? '1. 7-Day Money-Back Guarantee' : '1. Garantia de Devolução em 7 Dias'}>
            <p>{en
              ? 'We stand behind the quality of FinAnalyzer.AI. If you are not satisfied with the service for any reason, you may request a full refund within 7 calendar days of your first paid subscription charge.'
              : 'Acreditamos na qualidade do FinAnalyzer.AI. Se você não estiver satisfeito com o serviço por qualquer motivo, poderá solicitar reembolso integral em até 7 dias corridos a partir da data do primeiro pagamento de assinatura.'
            }</p>
            <p className="mt-3">{en
              ? 'Note: The 7-day free trial period is not counted toward the refund guarantee. The guarantee applies to the first paid charge after the trial ends.'
              : 'Observação: O período de trial gratuito de 7 dias não é contabilizado para a garantia de reembolso. A garantia se aplica ao primeiro pagamento efetuado após o encerramento do trial.'
            }</p>
          </Section>

          <Section icon={<RefreshCw size={18} className="text-purple-400" />} title={en ? '2. How to Request a Refund' : '2. Como Solicitar um Reembolso'}>
            <p>{en ? 'Follow these steps to request a refund:' : 'Siga estas etapas para solicitar um reembolso:'}</p>
            <ol className="mt-3 space-y-3 list-decimal list-inside">
              <li>{en
                ? <span>Send an email to <a href="mailto:finanalyserai@gmail.com" className="text-blue-400 hover:text-blue-300 transition-colors font-medium">finanalyserai@gmail.com</a> with the subject line "Refund Request".</span>
                : <span>Envie um e-mail para <a href="mailto:finanalyserai@gmail.com" className="text-blue-400 hover:text-blue-300 transition-colors font-medium">finanalyserai@gmail.com</a> com o assunto "Solicitação de Reembolso".</span>
              }</li>
              <li>{en ? 'Include your registered email address and the date of your payment.' : 'Inclua seu endereço de e-mail cadastrado e a data do seu pagamento.'}</li>
              <li>{en ? 'Attach proof of payment (Stripe receipt or bank statement).' : 'Anexe o comprovante de pagamento (recibo Stripe ou extrato bancário).'}</li>
              <li>{en ? 'Our team will respond within 1 business day and process the refund within 3 business days.' : 'Nossa equipe responderá em até 1 dia útil e processará o reembolso em até 3 dias úteis.'}</li>
            </ol>
          </Section>

          <Section icon={<XCircle size={18} className="text-red-400" />} title={en ? '3. Non-Refundable Situations' : '3. Situações Não Reembolsáveis'}>
            <p>{en ? 'Refunds will not be issued in the following cases:' : 'Reembolsos não serão concedidos nos seguintes casos:'}</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li>{en ? 'Requests made after the 7-day guarantee period has expired.' : 'Solicitações feitas após o vencimento do prazo de garantia de 7 dias.'}</li>
              <li>{en ? 'Partial months or years of service already used beyond the 7-day window.' : 'Meses ou anos parciais do serviço já utilizados fora do prazo de 7 dias.'}</li>
              <li>{en ? 'Accounts found to have violated our Terms of Use.' : 'Contas que violaram nossos Termos de Uso.'}</li>
              <li>{en ? 'Cancellations that occur after the automatic renewal date.' : 'Cancelamentos realizados após a data de renovação automática.'}</li>
            </ul>
          </Section>

          <Section icon={<Clock size={18} className="text-blue-400" />} title={en ? '4. Cancellation Policy' : '4. Política de Cancelamento'}>
            <p>{en
              ? 'You may cancel your subscription at any time through your account settings or by contacting us. Cancellation stops future charges but does not trigger a refund for the current billing period unless you are within the 7-day guarantee window.'
              : 'Você pode cancelar sua assinatura a qualquer momento pelas configurações da conta ou entrando em contato conosco. O cancelamento interrompe cobranças futuras, mas não gera reembolso pelo período de cobrança atual, exceto quando dentro do prazo de garantia de 7 dias.'
            }</p>
            <p className="mt-3">{en
              ? 'After cancellation, you retain access to the Platform until the end of your current paid billing period.'
              : 'Após o cancelamento, você mantém acesso à Plataforma até o final do período de cobrança pago atual.'
            }</p>
          </Section>

          <Section icon={<HelpCircle size={18} className="text-blue-400" />} title={en ? '5. Disputes & Chargebacks' : '5. Disputas e Chargebacks'}>
            <p>{en
              ? 'We ask that you contact us before initiating a chargeback with your bank or credit card provider. We are committed to resolving any issue promptly and fairly. Chargebacks initiated without prior contact may result in account suspension.'
              : 'Solicitamos que você nos contate antes de iniciar um chargeback com seu banco ou operadora de cartão. Estamos comprometidos em resolver qualquer problema de forma rápida e justa. Chargebacks iniciados sem contato prévio podem resultar em suspensão da conta.'
            }</p>
          </Section>

          {/* Contact CTA */}
          <div className="bg-purple-500/5 border border-purple-500/20 rounded-2xl p-6 flex items-start gap-4 mt-12">
            <Mail size={20} className="text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-semibold mb-1">{en ? 'Need help with a refund?' : 'Precisa de ajuda com reembolso?'}</p>
              <p className="text-gray-400 text-sm">
                {en ? 'Email us at ' : 'Envie um e-mail para '}
                <a href="mailto:finanalyserai@gmail.com" className="text-blue-400 hover:text-blue-300 transition-colors font-medium">
                  finanalyserai@gmail.com
                </a>
                {en
                  ? ' — we typically respond within 1 business day.'
                  : ' — respondemos em até 1 dia útil.'
                }
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-white/5 pb-10">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 bg-white/5 rounded-lg flex items-center justify-center flex-shrink-0">
          {icon}
        </div>
        <h2 className="text-lg font-bold text-white">{title}</h2>
      </div>
      <div className="text-gray-400 leading-relaxed text-sm space-y-2 ml-11">
        {children}
      </div>
    </div>
  );
}