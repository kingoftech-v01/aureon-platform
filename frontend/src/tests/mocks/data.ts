/**
 * Mock Data for Tests
 * Aureon by Rhematek Solutions
 */

import type { User, Client, Invoice, Contract, Payment } from '@/types';

export const mockUser: User = {
  id: '1',
  email: 'test@example.com',
  first_name: 'John',
  last_name: 'Doe',
  phone: '+1234567890',
  job_title: 'Software Engineer',
  is_active: true,
  is_staff: false,
  date_joined: '2024-01-01T00:00:00Z',
};

export const mockClient: Client = {
  id: '1',
  type: 'individual',
  first_name: 'Jane',
  last_name: 'Smith',
  email: 'jane@example.com',
  phone: '+1234567890',
  company_name: null,
  tax_id: null,
  address_line1: '123 Main St',
  address_line2: null,
  city: 'New York',
  state: 'NY',
  postal_code: '10001',
  country: 'USA',
  lifecycle_stage: 'lead',
  tags: ['vip'],
  notes: 'Test client',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockContract: Contract = {
  id: '1',
  contract_number: 'CNT-001',
  client: mockClient,
  title: 'Web Development Project',
  description: 'Build a new website',
  contract_type: 'fixed_price',
  status: 'active',
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  value: 10000,
  currency: 'USD',
  payment_terms: 'Net 30',
  milestones: [
    {
      id: '1',
      title: 'Design Phase',
      description: 'Complete UI/UX design',
      due_date: '2024-03-01',
      amount: 3000,
      status: 'completed',
      completed_at: '2024-02-28T00:00:00Z',
    },
    {
      id: '2',
      title: 'Development Phase',
      description: 'Build the application',
      due_date: '2024-06-01',
      amount: 5000,
      status: 'in_progress',
      completed_at: null,
    },
  ],
  terms_and_conditions: 'Standard terms apply',
  signed_at: '2024-01-01T00:00:00Z',
  signed_by_client: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockInvoice: Invoice = {
  id: '1',
  invoice_number: 'INV-001',
  client: mockClient,
  contract: mockContract,
  status: 'sent',
  issue_date: '2024-01-01',
  due_date: '2024-01-31',
  subtotal: 1000,
  tax_rate: 10,
  tax_amount: 100,
  discount_amount: 0,
  total: 1100,
  paid_amount: 0,
  notes: 'Thank you for your business',
  items: [
    {
      id: '1',
      description: 'Web Design Services',
      quantity: 10,
      unit_price: 100,
      amount: 1000,
    },
  ],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

export const mockPayment: Payment = {
  id: '1',
  invoice: mockInvoice,
  amount: 1100,
  payment_method: 'card',
  status: 'succeeded',
  transaction_id: 'txn_123456',
  payment_date: '2024-01-15T00:00:00Z',
  stripe_payment_intent_id: 'pi_123456',
  notes: 'Payment received',
  created_at: '2024-01-15T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
};

export const mockPaginatedResponse = <T>(items: T[], page = 1, pageSize = 10) => ({
  count: items.length,
  next: null,
  previous: null,
  results: items.slice((page - 1) * pageSize, page * pageSize),
});
