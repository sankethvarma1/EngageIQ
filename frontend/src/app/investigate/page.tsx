'use client';

import dynamic from 'next/dynamic';

const InvestigatePageContent = dynamic(
  () => import('./page-content').then((mod) => mod.default),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    ),
  }
);

export default function InvestigatePage() {
  return <InvestigatePageContent />;
}