"use client";
import { useLocale } from 'next-intl';
import Link from 'next/link';
import { BarChart3, ArrowLeft, Shield, FileText, CreditCard, AlertTriangle, Scale, Mail } from 'lucide-react';

export default function Terms() {
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
            <div className="w-12 h-12 bg-blue-500/10 border border-blue-500/20 rounded-2xl flex items-center justify-center">
              <FileText className="text-blue-400 w-6 h-6" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-3 tracking-tight">
            {en ? 'Terms of Use' : 'Termos de Uso'}
          </h1>
          <p className="text-gray-500 text-sm">
            {en ? 'Last updated: April 24, 2026' : 'Última atualização: 24 de Abril de 2026'}
          </p>
        </div>

        {/* Content */}
        <div className="space-y-10">

          <Section icon={<Scale size={18} className="text-blue-400" />} title={en ? '1. Acceptance of Terms' : '1. Aceitação dos Termos'}>
            <p>{en
              ? 'By accessing or using FinAnalyzer.AI ("the Platform"), you agree to be bound by these Terms of Use. If you do not agree with any part of these terms, you must not use the Platform. These terms apply to all users, including visitors, registered users, and subscribers.'
              : 'Ao acessar ou utilizar o FinAnalyzer.AI ("a Plataforma"), você concorda em se vincular a estes Termos de Uso. Caso não concorde com qualquer parte destes termos, você não deverá utilizar a Plataforma. Estes termos se aplicam a todos os usuários, incluindo visitantes, usuários registrados e assinantes.'
            }</p>
          </Section>

          <Section icon={<BarChart3 size={18} className="text-blue-400" />} title={en ? '2. Description of Service' : '2. Descrição do Serviço'}>
            <p>{en
              ? 'FinAnalyzer.AI is an artificial intelligence-powered financial analysis tool that processes quarterly earnings reports (PDFs) and earnings call transcripts provided by the user. The Platform generates automated reports, scores, and investment theses based on the submitted documents.'
              : 'O FinAnalyzer.AI é uma ferramenta de análise financeira baseada em inteligência artificial que processa relatórios de resultados trimestrais (PDFs) e transcrições de earnings calls fornecidos pelo usuário. A Plataforma gera relatórios automatizados, notas e teses de investimento com base nos documentos enviados.'
            }</p>
            <p className="mt-3">{en
              ? 'The analyses generated are for informational and educational purposes only. They do not constitute investment advice, financial recommendations, or solicitation to buy or sell any securities.'
              : 'As análises geradas são exclusivamente para fins informativos e educacionais. Elas não constituem aconselhamento de investimento, recomendação financeira ou solicitação de compra ou venda de quaisquer valores mobiliários.'
            }</p>
          </Section>

          <Section icon={<CreditCard size={18} className="text-blue-400" />} title={en ? '3. Free Trial & Subscriptions' : '3. Trial Gratuito & Assinaturas'}>
            <p>{en
              ? 'New users receive a 7-day free trial with full access to all Platform features. No credit card is required to start the trial. After the trial period ends, continued access requires an active paid subscription.'
              : 'Novos usuários recebem um trial gratuito de 7 dias com acesso completo a todas as funcionalidades da Plataforma. Não é necessário cartão de crédito para iniciar o trial. Após o término do período de trial, o acesso continuado requer uma assinatura paga ativa.'
            }</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li>{en ? 'Monthly plan: R$ 29/month, billed monthly.' : 'Plano Mensal: R$ 29/mês, cobrado mensalmente.'}</li>
              <li>{en ? 'Annual plan: R$ 290/year, billed annually (equivalent to 2 free months).' : 'Plano Anual: R$ 290/ano, cobrado anualmente (equivalente a 2 meses gratuitos).'}</li>
              <li>{en ? 'Subscriptions renew automatically until cancelled.' : 'As assinaturas renovam automaticamente até serem canceladas.'}</li>
              <li>{en ? 'You may cancel your subscription at any time before the next billing cycle.' : 'Você pode cancelar sua assinatura a qualquer momento antes do próximo ciclo de cobrança.'}</li>
            </ul>
          </Section>

          <Section icon={<Shield size={18} className="text-blue-400" />} title={en ? '4. Acceptable Use' : '4. Uso Aceitável'}>
            <p>{en ? 'You agree not to:' : 'Você concorda em não:'}</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li>{en ? 'Use the Platform for any unlawful purpose.' : 'Utilizar a Plataforma para qualquer finalidade ilegal.'}</li>
              <li>{en ? 'Upload documents containing malicious code or unauthorized third-party content.' : 'Enviar documentos contendo código malicioso ou conteúdo de terceiros sem autorização.'}</li>
              <li>{en ? 'Attempt to reverse-engineer, scrape, or extract the underlying AI models.' : 'Tentar fazer engenharia reversa, raspagem ou extração dos modelos de IA subjacentes.'}</li>
              <li>{en ? 'Share your account credentials with others.' : 'Compartilhar suas credenciais de acesso com terceiros.'}</li>
              <li>{en ? 'Resell or redistribute the Platform\'s outputs without prior written consent.' : 'Revender ou redistribuir os resultados da Plataforma sem consentimento prévio por escrito.'}</li>
            </ul>
          </Section>

          <Section icon={<AlertTriangle size={18} className="text-amber-400" />} title={en ? '5. Disclaimer & Limitation of Liability' : '5. Isenção de Responsabilidade'}>
            <p>{en
              ? 'THE PLATFORM PROVIDES INFORMATION GENERATED BY ARTIFICIAL INTELLIGENCE AND MAKES NO WARRANTIES, EXPRESS OR IMPLIED, AS TO THE ACCURACY, COMPLETENESS, OR FITNESS FOR ANY PARTICULAR PURPOSE OF SUCH INFORMATION.'
              : 'A PLATAFORMA FORNECE INFORMAÇÕES GERADAS POR INTELIGÊNCIA ARTIFICIAL E NÃO OFERECE GARANTIAS, EXPRESSAS OU IMPLÍCITAS, QUANTO À PRECISÃO, INTEGRIDADE OU ADEQUAÇÃO DAS INFORMAÇÕES PARA QUALQUER FINALIDADE ESPECÍFICA.'
            }</p>
            <p className="mt-3">{en
              ? 'FinAnalyzer.AI and its operators shall not be liable for any direct, indirect, incidental, or consequential damages resulting from investment decisions made based on the Platform\'s analyses. Past performance data displayed is not indicative of future results.'
              : 'O FinAnalyzer.AI e seus operadores não serão responsáveis por quaisquer danos diretos, indiretos, incidentais ou consequenciais resultantes de decisões de investimento tomadas com base nas análises da Plataforma. Dados de desempenho passado exibidos não são indicativos de resultados futuros.'
            }</p>
          </Section>

          <Section icon={<FileText size={18} className="text-blue-400" />} title={en ? '6. Intellectual Property' : '6. Propriedade Intelectual'}>
            <p>{en
              ? 'All content, technology, design, and AI models comprising the Platform are the exclusive property of FinAnalyzer.AI. You retain ownership of the documents you upload. By submitting documents, you grant FinAnalyzer.AI a limited, non-exclusive license to process them solely for the purpose of providing the Service.'
              : 'Todo o conteúdo, tecnologia, design e modelos de IA que compõem a Plataforma são propriedade exclusiva do FinAnalyzer.AI. Você mantém a propriedade dos documentos que envia. Ao enviar documentos, você concede ao FinAnalyzer.AI uma licença limitada e não exclusiva para processá-los exclusivamente com o objetivo de fornecer o Serviço.'
            }</p>
          </Section>

          <Section icon={<Scale size={18} className="text-blue-400" />} title={en ? '7. Governing Law' : '7. Lei Aplicável'}>
            <p>{en
              ? 'These Terms are governed by the laws of Brazil. Any disputes arising from these Terms shall be subject to the exclusive jurisdiction of the courts of São Paulo, Brazil.'
              : 'Estes Termos são regidos pelas leis do Brasil. Quaisquer disputas decorrentes destes Termos estarão sujeitas à jurisdição exclusiva dos tribunais de São Paulo, Brasil.'
            }</p>
          </Section>

          <Section icon={<Scale size={18} className="text-blue-400" />} title={en ? '8. Modifications' : '8. Modificações'}>
            <p>{en
              ? 'We reserve the right to modify these Terms at any time. Changes will be effective upon posting to the Platform. Continued use of the Platform after changes constitutes acceptance of the new terms.'
              : 'Reservamo-nos o direito de modificar estes Termos a qualquer momento. As alterações entrarão em vigor após a publicação na Plataforma. O uso continuado da Plataforma após as alterações constitui aceitação dos novos termos.'
            }</p>
          </Section>

          {/* Contact */}
          <div className="bg-blue-500/5 border border-blue-500/20 rounded-2xl p-6 flex items-start gap-4 mt-12">
            <Mail size={20} className="text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-white font-semibold mb-1">{en ? 'Questions?' : 'Dúvidas?'}</p>
              <p className="text-gray-400 text-sm">{en
                ? 'Contact us at '
                : 'Entre em contato pelo e-mail '}
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