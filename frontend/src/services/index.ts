/**
 * API Services Barrel Export
 * Aureon by Rhematek Solutions
 */

export { default as apiClient, tokenService, uploadFile, downloadFile } from './api';
export { default as authService } from './authService';
export { default as clientService } from './clientService';
export { default as contractService } from './contractService';
export { default as invoiceService } from './invoiceService';
export { default as paymentService } from './paymentService';
export { default as analyticsService } from './analyticsService';
export { default as notificationService } from './notificationService';
export { default as documentService } from './documentService';
export { default as tenantService } from './tenantService';
export { default as webhookService } from './webhookService';
export { default as marketingService } from './marketingService';

// Re-export types for convenience
export type * from '@/types';
