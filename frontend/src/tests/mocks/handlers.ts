/**
 * MSW Mock Handlers
 * Aureon by Rhematek Solutions
 *
 * Mock API handlers for testing
 */

import { http, HttpResponse } from 'msw';
import { mockUser, mockClient, mockInvoice, mockContract, mockPayment, mockPaginatedResponse } from './data';

const API_BASE = 'http://localhost:8000/api';

export const handlers = [
  // Auth endpoints
  http.post(`${API_BASE}/auth/login/`, () => {
    return HttpResponse.json({
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      user: mockUser,
    });
  }),

  http.post(`${API_BASE}/auth/register/`, () => {
    return HttpResponse.json({
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      user: mockUser,
    });
  }),

  http.get(`${API_BASE}/auth/user/`, () => {
    return HttpResponse.json(mockUser);
  }),

  // Clients endpoints
  http.get(`${API_BASE}/clients/`, () => {
    return HttpResponse.json(mockPaginatedResponse([mockClient]));
  }),

  http.get(`${API_BASE}/clients/:id/`, () => {
    return HttpResponse.json(mockClient);
  }),

  http.post(`${API_BASE}/clients/`, () => {
    return HttpResponse.json(mockClient);
  }),

  // Contracts endpoints
  http.get(`${API_BASE}/contracts/`, () => {
    return HttpResponse.json(mockPaginatedResponse([mockContract]));
  }),

  http.get(`${API_BASE}/contracts/:id/`, () => {
    return HttpResponse.json(mockContract);
  }),

  // Invoices endpoints
  http.get(`${API_BASE}/invoices/`, () => {
    return HttpResponse.json(mockPaginatedResponse([mockInvoice]));
  }),

  http.get(`${API_BASE}/invoices/:id/`, () => {
    return HttpResponse.json(mockInvoice);
  }),

  // Payments endpoints
  http.get(`${API_BASE}/payments/`, () => {
    return HttpResponse.json(mockPaginatedResponse([mockPayment]));
  }),
];
