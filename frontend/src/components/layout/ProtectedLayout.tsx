import { Outlet } from 'react-router-dom';
import { ProtectedRoute } from '@/contexts/AuthContext';
import Layout from './Layout';

export default function ProtectedLayout() {
  return (
    <ProtectedRoute>
      <Layout>
        <Outlet />
      </Layout>
    </ProtectedRoute>
  );
}
