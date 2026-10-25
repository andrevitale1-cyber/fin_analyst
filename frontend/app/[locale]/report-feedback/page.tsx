import ReportFeedback from "../../../components/ReportFeedback";

export const metadata = { robots: { index: false, follow: false } };

export default async function FeedbackPage({ params, searchParams }: { params: Promise<{locale: string}>; searchParams: Promise<{report?: string}> }) {
  const { locale } = await params;
  const { report } = await searchParams;
  if (!report || !/^editorial-(aapl|nvda)-20261022$/.test(report)) return null;
  return <ReportFeedback reportId={report} locale={locale}/>;
}
