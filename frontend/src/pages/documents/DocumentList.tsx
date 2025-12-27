import React from 'react';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';

const DocumentList: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Documents</h1>
      <Card><CardHeader><CardTitle>Document Vault</CardTitle></CardHeader><CardContent><p className="text-gray-600 dark:text-gray-400">Document management coming soon...</p></CardContent></Card>
    </div>
  );
};
export default DocumentList;
