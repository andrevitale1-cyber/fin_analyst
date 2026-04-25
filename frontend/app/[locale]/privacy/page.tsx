"use client";
import { useLocale } from 'next-intl';
import Link from 'next/link';
import { BarChart3, ArrowLeft, Lock, Eye, Database, Server, Mail, UserCheck } from 'lucide-react';

export default function Privacy() {
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
            <div className="w-12 h-12 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center justify-center">
              <Lock className="text-emerald-400 w-6 h-6" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
            {en ? 'Privacy Policy' : 'Política de Privacidade'}
          </h1>
          <p className="text-gray-500 text-sm">
            {en ? 'Last updated: April 24, 2026' : 'Última atualização: 24 de Abril de 2026'}
          </p>
        </div>

        <div className="space-y-10">

          <Section icon={<Eye size={18} className="text-emerald-400" />} title={en ? '1. What Data We Collect' : '1. Quais Dados Coletamos'}>
            <p>{en
              ? 'We collect only the minimum data necessary to provide the Service:'
              : 'Coletamos apenas os dados mínimos necessários para fornecer o Serviço:'
            }</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li><strong className="text-gray-300">{en ? 'Account data:' : 'Dados de conta:'}</strong> {en ? 'name and email address collected via Clerk for authentication.' : 'nome e endereço de e-mail coletados via Clerk para autenticação.'}</li>
              <li><strong className="text-gray-300">{en ? 'Payment data:' : 'Dados de pagamento:'}</strong> {en ? 'billing information processed securely by Stripe. We never store card numbers.' : 'informações de cobrança processadas com segurança pelo Stripe. Nunca armazenamos números de cartão.'}</li>
              <li><strong className="text-gray-300">{en ? 'Usage data:' : 'Dados de uso:'}</strong> {en ? 'analyses performed and analysis history, linked to your account ID.' : 'análises realizadas e histórico de análises, vinculados ao seu ID de conta.'}</li>
              <li><strong className="text-gray-300">{en ? 'Uploaded documents:' : 'Documentos enviados:'}</strong> {en ? 'PDF files submitted for analysis. These are processed in memory and not permanently stored on our servers.' : 'arquivos PDF enviados para análise. Esses arquivos são processados em memória e não armazenados permanentemente em nossos servidores.'}</li>
            </ul>
          </Section>

          <Section icon={<Database size={18} className="text-emerald-400" />} title={en ? '2. How We Use Your Data' : '2. Como Usamos Seus Dados'}>
            <p>{en ? 'Your data is used exclusively to:' : 'Seus dados são usados exclusivamente para:'}</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li>{en ? 'Authenticate your identity and manage your account.' : 'Autenticar sua identidade e gerenciar sua conta.'}</li>
              <li>{en ? 'Process and return AI-generated financial analyses.' : 'Processar e retornar análises financeiras geradas por IA.'}</li>
              <li>{en ? 'Manage your subscription and billing.' : 'Gerenciar sua assinatura e cobrança.'}</li>
              <li>{en ? 'Store your analysis history for future reference.' : 'Armazenar seu histórico de análises para referência futura.'}</li>
              <li>{en ? 'Send transactional emails (e.g., payment confirmations).' : 'Enviar e-mails transacionais (ex.: confirmações de pagamento).'}</li>
            </ul>
            <p className="mt-3 font-semibold text-gray-300">{en
              ? 'We do not sell, rent, or share your personal data with third parties for marketing purposes.'
              : 'Não vendemos, alugamos ou compartilhamos seus dados pessoais com terceiros para fins de marketing.'
            }</p>
          </Section>

          <Section icon={<Server size={18} className="text-emerald-400" />} title={en ? '3. Third-Party Services' : '3. Serviços de Terceiros'}>
            <p>{en
              ? 'We use trusted third-party providers to operate the Platform. Each provider processes your data only as necessary for their specific function:'
              : 'Utilizamos provedores terceiros de confiança para operar a Plataforma. Cada provedor processa seus dados apenas na medida necessária para sua função específica:'
            }</p>
            <ul className="mt-4 space-y-3">
              {[
                { name: 'Clerk', role: en ? 'Authentication and user management' : 'Autenticação e gerenciamento de usuários', url: 'https://clerk.com' },
                { name: 'Stripe', role: en ? 'Payment processing' : 'Processamento de pagamentos', url: 'https://stripe.com' },
                { name: 'Google Gemini (AI)', role: en ? 'AI analysis generation — documents are processed but not used to train their models' : 'Geração de análises por IA — documentos são processados mas não usados para treinar seus modelos', url: 'https://ai.google.dev' },
                { name: 'Vercel', role: en ? 'Frontend hosting and delivery' : 'Hospedagem e entrega do frontend', url: 'https://vercel.com' },
                { name: 'Render / Neon', role: en ? 'Backend hosting and database' : 'Hospedagem do backend e banco de dados', url: 'https://render.com' },
              ].map(p => (
                <li key={p.name} className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0 mt-1.5" />
                  <span><strong className="text-gray-300">{p.name}:</strong> {p.role}</span>
                </li>
              ))}
            </ul>
          </Section>

          <Section icon={<Lock size={18} className="text-emerald-400" />} title={en ? '4. Data Security' : '4. Segurança dos Dados'}>
            <p>{en
              ? 'We implement industry-standard security measures to protect your data:'
              : 'Implementamos medidas de segurança padrão do setor para proteger seus dados:'
            }</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li>{en ? 'All data transmitted is encrypted via HTTPS/TLS.' : 'Todos os dados transmitidos são criptografados via HTTPS/TLS.'}</li>
              <li>{en ? 'Passwords are never stored — authentication is handled entirely by Clerk.' : 'Senhas nunca são armazenadas — a autenticação é gerenciada inteiramente pelo Clerk.'}</li>
              <li>{en ? 'Database access is restricted and uses encrypted connections.' : 'O acesso ao banco de dados é restrito e utiliza conexões criptografadas.'}</li>
              <li>{en ? 'Uploaded PDFs are processed in memory and not written to disk permanently.' : 'PDFs enviados são processados em memória e não gravados em disco permanentemente.'}</li>
            </ul>
          </Section>

          <Section icon={<UserCheck size={18} className="text-emerald-400" />} title={en ? '5. Your Rights' : '5. Seus Direitos'}>
            <p>{en
              ? 'In accordance with applicable data protection laws (including Brazil\'s LGPD), you have the right to:'
              : 'Em conformidade com as leis de proteção de dados aplicáveis (incluindo a LGPD brasileira), você tem o direito de:'
            }</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li>{en ? 'Access the personal data we hold about you.' : 'Acessar os dados pessoais que mantemos sobre você.'}</li>
              <li>{en ? 'Request correction of inaccurate data.' : 'Solicitar correção de dados imprecisos.'}</li>
              <li>{en ? 'Request deletion of your account and associated data.' : 'Solicitar exclusão de sua conta e dados associados.'}</li>
              <li>{en ? 'Withdraw consent at any time by deleting your account.' : 'Retirar o consentimento a qualquer momento excluindo sua conta.'}</li>
            </ul>
            <p className="mt-3">{en
              ? 'To exercise any of these rights, contact us at '
              : 'Para exercer qualquer desses direitos, entre em contato pelo e-mail '}
              <a href="mailto:finanalyserai@gmail.com" className="text-blue-400 hover:text-blue-300 transition-colors font-medium">
                finanalyserai@gmail.com
              </a>
            </p>
          </Section>

          <Section icon={<Eye size={18} className="text-emerald-400" />} title={en ? '6. Cookies' : '6. Cookies'}>
            <p>{en
              ? 'We use only essential cookies required for authentication (managed by Clerk) and session management. We do not use tracking or advertising cookies.'
              : 'Utilizamos apenas cookies essenciais necessários para autenticação (gerenciados pelo Clerk) e gerenciamento de sessão. Não utilizamos cookies de rastreamento ou publicidade.'
            }</p>
          </Section>

          <Section icon={<Lock size={18} className="text-emerald-400" />} title={en ? '7. Changes to This Policy' : '7. Alterações nesta Política'}>
            <p>{en
              ? 'We may update this Privacy Policy periodically. We will notify registered users of material changes via email. Your continued use of the Platform after changes constitutes acceptance of the updated policy.'
              : 'Podemos atualizar esta Política de Privacidade periodicamente. Notificaremos usuários registrados sobre alterações materiais por e-mail. O uso continuado da Plataforma após as alterações constitui aceitação da política atualizada.'
            }</p>
          </Section>

          {/* Contact */}
          <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-6 flex items-start gap-4 mt-12">
            <Mail size={20} className="text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-semibold mb-1">{en ? 'Privacy questions?' : 'Dúvidas sobre privacidade?'}</p>
              <p className="text-gray-400 text-sm">{en
                ? 'Contact our Data Protection team at '
                : 'Entre em contato com nossa equipe pelo e-mail '}
                <a href="mailto:finanalyserai@gmail.com" className="text-blue-400 hover:text-blue-300 transition-colors font-medium">
                  finanalyserai@gmail.com
                </a>
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