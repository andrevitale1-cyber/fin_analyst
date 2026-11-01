import type { Metadata } from "next";
import TrialAccessGate from '../../../components/TrialAccessGate';

export const metadata: Metadata = {
  title: "Dashboard",
  robots: { index: false, follow: false },
};

export default function DashboardLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return <TrialAccessGate>{children}</TrialAccessGate>;
}
