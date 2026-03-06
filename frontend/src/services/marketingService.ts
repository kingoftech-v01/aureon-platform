/**
 * Marketing Service
 * Aureon by Rhematek Solutions
 *
 * API methods for public marketing pages: contact form, newsletter, and FAQs
 */

import api from './api';

export const marketingService = {
  submitContactForm: (data: { name: string; email: string; subject: string; message: string }) =>
    api.post('/website/contact/', data),

  subscribeNewsletter: (email: string) =>
    api.post('/website/newsletter/', { email }),

  getFAQs: () =>
    api.get('/website/faqs/'),
};

export default marketingService;
