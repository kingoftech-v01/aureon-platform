const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://aureon.rhematek-solutions.com/api/v1';

export const apiClient = {
  async get(endpoint) {
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }
      return res.json();
    } catch (error) {
      console.error('API Error:', error);
      return null;
    }
  },

  async post(endpoint, data) {
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      return res.json();
    } catch (error) {
      console.error('API Error:', error);
      return { error: error.message };
    }
  },
};

// Marketing API endpoints
export const marketingApi = {
  // Services
  getServices: () => apiClient.get('/website/services/'),
  getService: (slug) => apiClient.get(`/website/services/${slug}/`),

  // Pricing
  getPricingPlans: () => apiClient.get('/website/pricing/'),

  // Testimonials
  getTestimonials: () => apiClient.get('/website/testimonials/'),

  // Blog
  getBlogPosts: () => apiClient.get('/website/posts/'),
  getBlogPost: (slug) => apiClient.get(`/website/posts/${slug}/`),
  getBlogCategories: () => apiClient.get('/website/categories/'),

  // FAQ
  getFAQs: () => apiClient.get('/website/faqs/'),

  // Contact
  submitContact: (data) => apiClient.post('/website/contact/', data),
  subscribeNewsletter: (email) => apiClient.post('/website/newsletter/', { email }),

  // Case Studies
  getCaseStudies: () => apiClient.get('/website/case-studies/'),
  getCaseStudy: (slug) => apiClient.get(`/website/case-studies/${slug}/`),

  // Site Settings
  getSiteSettings: () => apiClient.get('/website/settings/'),
};

export default marketingApi;
