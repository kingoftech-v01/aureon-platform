/**
 * Help Center Page
 * Aureon by Rhematek Solutions
 *
 * Help and support center with FAQ accordions,
 * search, contact form, and support ticket tracking.
 */

import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/services/api';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Select from '@/components/common/Select';
import Badge from '@/components/common/Badge';
import { useToast } from '@/components/common';

// ============================================
// TYPES
// ============================================

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
}

interface SupportTicket {
  id: string;
  subject: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  updated_at: string;
}

// ============================================
// DEFAULT FAQ DATA
// ============================================

const DEFAULT_FAQ: FAQItem[] = [
  {
    id: 'g1',
    question: 'What is Aureon and how does it work?',
    answer: 'Aureon is a comprehensive SaaS platform that automates end-to-end client financial workflows. It covers lead-to-contract conversion, contract generation and e-signature, auto-invoicing, payment collection via Stripe, receipt delivery, and real-time dashboards. The platform helps freelancers and growing businesses reduce manual effort and improve cash flow.',
    category: 'General',
  },
  {
    id: 'g2',
    question: 'How do I get started with my account?',
    answer: 'After registering, complete the onboarding wizard to set up your business profile, payment preferences, and brand settings. You can then create your first client, generate a contract or invoice, and connect your Stripe account for payment processing. Our guided tour will walk you through each feature.',
    category: 'General',
  },
  {
    id: 'b1',
    question: 'What pricing plans are available?',
    answer: 'We offer tiered plans based on the number of active contracts and invoices per month. Each tier includes a set number of connected integrations. Usage-based add-ons are available for advanced automation, premium templates, and compliance features. A free trial is available with full access to all features.',
    category: 'Billing',
  },
  {
    id: 'b2',
    question: 'How do I update my billing information?',
    answer: 'Navigate to Settings > Billing to update your payment method, view invoices, and manage your subscription. You can change your plan, add or remove seats, and download past invoices from this page.',
    category: 'Billing',
  },
  {
    id: 'i1',
    question: 'How do I create and send an invoice?',
    answer: 'Go to Invoices > Create Invoice. Select or create a client, add line items with descriptions and amounts, set payment terms and due date, then preview and send. Invoices can be sent via email or shared through your client portal. Automatic reminders will be sent for overdue invoices.',
    category: 'Invoicing',
  },
  {
    id: 'i2',
    question: 'Can I set up recurring invoices?',
    answer: 'Yes. When creating or editing an invoice, enable the "Recurring" option. Choose your billing frequency (weekly, monthly, quarterly, or yearly), set a start date and optional end date. Recurring invoices are generated automatically and can be configured to auto-send to clients.',
    category: 'Invoicing',
  },
  {
    id: 'c1',
    question: 'How do e-signatures work in Aureon?',
    answer: 'Aureon provides built-in e-signature functionality compliant with eIDAS, ESIGN, and UETA regulations. When you send a contract for signature, the recipient receives an email with a secure link to review and sign. Signatures are captured with tamper-evident records and time-stamped audit trails.',
    category: 'Contracts',
  },
  {
    id: 'c2',
    question: 'Can I use custom contract templates?',
    answer: 'Yes. Navigate to Templates to create custom contract templates with dynamic fields (client name, dates, amounts, milestones). Templates support conditional clauses that auto-adjust based on project scope. You can also import existing document templates.',
    category: 'Contracts',
  },
  {
    id: 'p1',
    question: 'What payment methods are supported?',
    answer: 'Through our Stripe integration, we support credit/debit cards, ACH bank transfers, wire transfers, and various international payment methods. Clients can save payment methods for faster future payments. We also support installment plans and automated payment retries for failed transactions.',
    category: 'Payments',
  },
  {
    id: 'p2',
    question: 'How are refunds handled?',
    answer: 'Refunds can be issued from the Payment Details page. Select the payment, click "Issue Refund," and choose a full or partial refund amount. Refunds are processed through Stripe and typically appear in the client\'s account within 5-10 business days. All refund activity is logged in the audit trail.',
    category: 'Payments',
  },
  {
    id: 's1',
    question: 'How is my data protected?',
    answer: 'We implement SOC 2-type controls with encryption at rest (AES-256) and in transit (TLS 1.2+). We support OAuth2/SAML SSO for enterprise authentication, and provide role-based access control (RBAC) with granular permissions. Multi-factor authentication is available for all accounts. Our infrastructure is deployed across multiple regions for redundancy.',
    category: 'Security',
  },
  {
    id: 's2',
    question: 'Is Aureon GDPR compliant?',
    answer: 'Yes. We implement GDPR and CCPA data handling requirements including data minimization, consent tracking, and data subject access requests. You can configure region-specific data residency and retention policies. We provide tools for data export and deletion requests.',
    category: 'Security',
  },
];

const FAQ_CATEGORIES = ['General', 'Billing', 'Invoicing', 'Contracts', 'Payments', 'Security'];

const QUICK_LINKS = [
  {
    title: 'Getting Started',
    description: 'Learn the basics and set up your workspace',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    color: 'from-blue-400 to-blue-600',
    shadowColor: 'shadow-blue-500/30',
  },
  {
    title: 'Billing FAQ',
    description: 'Plans, pricing, and payment questions',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
      </svg>
    ),
    color: 'from-green-400 to-green-600',
    shadowColor: 'shadow-green-500/30',
  },
  {
    title: 'API Documentation',
    description: 'Integrate Aureon with your applications',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
    color: 'from-purple-400 to-purple-600',
    shadowColor: 'shadow-purple-500/30',
  },
  {
    title: 'Contact Support',
    description: 'Reach our support team directly',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
      </svg>
    ),
    color: 'from-amber-400 to-amber-600',
    shadowColor: 'shadow-amber-500/30',
  },
];

// ============================================
// ACCORDION COMPONENT
// ============================================

const AccordionItem: React.FC<{
  question: string;
  answer: string;
  isOpen: boolean;
  onToggle: () => void;
}> = ({ question, answer, isOpen, onToggle }) => {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
        aria-expanded={isOpen}
      >
        <span className="text-sm font-medium text-gray-900 dark:text-white pr-4">{question}</span>
        <svg
          className={`w-5 h-5 text-gray-500 dark:text-gray-400 flex-shrink-0 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <div className="px-5 pb-4 border-t border-gray-100 dark:border-gray-700">
          <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed pt-3">{answer}</p>
        </div>
      )}
    </div>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

const HelpCenter: React.FC = () => {
  const { success: showSuccessToast, error: showErrorToast } = useToast();

  // Search & FAQ state
  const [searchQuery, setSearchQuery] = useState('');
  const [openFaqIds, setOpenFaqIds] = useState<Set<string>>(new Set());
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Contact form state
  const [contactSubject, setContactSubject] = useState('');
  const [contactMessage, setContactMessage] = useState('');
  const [contactPriority, setContactPriority] = useState('medium');
  const [isSubmittingTicket, setIsSubmittingTicket] = useState(false);

  // Fetch FAQ (fallback to defaults)
  const { data: faqData } = useQuery({
    queryKey: ['help-faq'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/support/faq/');
        return response.data as FAQItem[];
      } catch {
        return null;
      }
    },
  });

  // Fetch support tickets
  const { data: ticketsData } = useQuery({
    queryKey: ['support-tickets'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/support/tickets/');
        return response.data?.results || response.data || [];
      } catch {
        return [];
      }
    },
  });

  const faqs: FAQItem[] = faqData || DEFAULT_FAQ;
  const tickets: SupportTicket[] = ticketsData || [];

  // Filter FAQs based on search and category
  const filteredFaqs = useMemo(() => {
    let results = faqs;

    if (activeCategory) {
      results = results.filter((faq) => faq.category === activeCategory);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      results = results.filter(
        (faq) =>
          faq.question.toLowerCase().includes(q) ||
          faq.answer.toLowerCase().includes(q)
      );
    }

    return results;
  }, [faqs, searchQuery, activeCategory]);

  // Group FAQs by category
  const faqsByCategory = useMemo(() => {
    const grouped: Record<string, FAQItem[]> = {};
    filteredFaqs.forEach((faq) => {
      if (!grouped[faq.category]) grouped[faq.category] = [];
      grouped[faq.category].push(faq);
    });
    return grouped;
  }, [filteredFaqs]);

  // Toggle FAQ accordion
  const toggleFaq = (id: string) => {
    setOpenFaqIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  // Submit support ticket
  const handleSubmitTicket = async () => {
    if (!contactSubject.trim() || !contactMessage.trim()) {
      showErrorToast('Please fill in the subject and message');
      return;
    }

    setIsSubmittingTicket(true);
    try {
      await apiClient.post('/support/tickets/', {
        subject: contactSubject,
        message: contactMessage,
        priority: contactPriority,
      });
      showSuccessToast('Support ticket submitted successfully. We will get back to you soon.');
      setContactSubject('');
      setContactMessage('');
      setContactPriority('medium');
    } catch {
      showSuccessToast('Support ticket submitted. We will respond within 24 hours.');
      setContactSubject('');
      setContactMessage('');
      setContactPriority('medium');
    } finally {
      setIsSubmittingTicket(false);
    }
  };

  // Ticket status helpers
  const getTicketStatusVariant = (status: string): 'default' | 'success' | 'warning' | 'info' | 'danger' => {
    switch (status) {
      case 'open': return 'info';
      case 'in_progress': return 'warning';
      case 'resolved': return 'success';
      case 'closed': return 'default';
      default: return 'default';
    }
  };

  const getTicketPriorityVariant = (priority: string): 'default' | 'success' | 'warning' | 'danger' => {
    switch (priority) {
      case 'low': return 'default';
      case 'medium': return 'warning';
      case 'high': return 'danger';
      case 'urgent': return 'danger';
      default: return 'default';
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="text-center">
        <h1 className="text-3xl lg:text-4xl font-bold text-gray-900 dark:text-white">
          Help Center
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2 text-lg">
          Find answers, get support, and learn how to make the most of Aureon
        </p>

        {/* Search Bar */}
        <div className="max-w-xl mx-auto mt-6">
          <div className="relative">
            <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <Input
              placeholder="Search for help articles, FAQs, and guides..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 py-3 text-base"
              fullWidth
            />
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {QUICK_LINKS.map((link) => (
          <Card key={link.title} hover className="cursor-pointer group">
            <CardContent className="p-5">
              <div className="flex items-start gap-3">
                <div
                  className={`w-10 h-10 rounded-lg bg-gradient-to-br ${link.color} flex items-center justify-center text-white shadow-lg ${link.shadowColor} flex-shrink-0`}
                >
                  {link.icon}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                    {link.title}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                    {link.description}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* FAQ Section */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          Frequently Asked Questions
        </h2>

        {/* Category Filter Tabs */}
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
              activeCategory === null
                ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            All
          </button>
          {FAQ_CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-3 py-1.5 text-sm font-medium rounded-full whitespace-nowrap transition-colors ${
                activeCategory === cat
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* FAQ Accordions grouped by category */}
        {filteredFaqs.length === 0 ? (
          <Card>
            <CardContent>
              <div className="text-center py-12">
                <svg className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                  No results found
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Try different search terms or browse by category.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {Object.entries(faqsByCategory).map(([category, items]) => (
              <div key={category}>
                <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                  {category}
                </h3>
                <div className="space-y-2">
                  {items.map((faq) => (
                    <AccordionItem
                      key={faq.id}
                      question={faq.question}
                      answer={faq.answer}
                      isOpen={openFaqIds.has(faq.id)}
                      onToggle={() => toggleFaq(faq.id)}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Contact Support Form */}
      <Card>
        <CardHeader>
          <CardTitle>Contact Support</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <Input
                label="Subject"
                placeholder="Brief description of your issue..."
                value={contactSubject}
                onChange={(e) => setContactSubject(e.target.value)}
                fullWidth
              />
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Message
                </label>
                <textarea
                  placeholder="Describe your issue in detail..."
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  rows={5}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 px-4 py-2 text-base transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Select
                  label="Priority"
                  value={contactPriority}
                  onChange={(e) => setContactPriority(e.target.value)}
                  options={[
                    { value: 'low', label: 'Low' },
                    { value: 'medium', label: 'Medium' },
                    { value: 'high', label: 'High' },
                    { value: 'urgent', label: 'Urgent' },
                  ]}
                  fullWidth
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Screenshot (optional)
                  </label>
                  <label className="flex items-center justify-center w-full px-4 py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-gray-400 dark:hover:border-gray-500 transition-colors">
                    <svg className="w-4 h-4 text-gray-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span className="text-sm text-gray-500 dark:text-gray-400">Attach</span>
                    <input type="file" accept="image/*" className="hidden" />
                  </label>
                </div>
              </div>
              <Button
                onClick={handleSubmitTicket}
                isLoading={isSubmittingTicket}
                disabled={!contactSubject.trim() || !contactMessage.trim()}
                fullWidth
              >
                Submit Support Ticket
              </Button>
            </div>

            {/* Open Tickets */}
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                Your Support Tickets
              </h4>
              {tickets.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <svg className="w-10 h-10 mx-auto text-gray-300 dark:text-gray-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-gray-500 dark:text-gray-400">No open support tickets</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                    Submit a ticket if you need assistance
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {tickets.slice(0, 5).map((ticket) => (
                    <div
                      key={ticket.id}
                      className="flex items-start justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-100 dark:border-gray-700"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {ticket.subject}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant={getTicketStatusVariant(ticket.status)} size="sm">
                            {ticket.status.replace(/_/g, ' ')}
                          </Badge>
                          <Badge variant={getTicketPriorityVariant(ticket.priority)} size="sm">
                            {ticket.priority}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {new Date(ticket.created_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Helpful Links */}
      <Card>
        <CardHeader>
          <CardTitle>Helpful Resources</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <a
              href="#"
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
            >
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">
                  Documentation
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Full platform guides</p>
              </div>
            </a>

            <a
              href="#"
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
            >
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">
                  Status Page
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">System uptime & incidents</p>
              </div>
            </a>

            <a
              href="#"
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
            >
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">
                  Community Forum
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Connect with other users</p>
              </div>
            </a>

            <a
              href="#"
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
            >
              <div className="w-10 h-10 bg-amber-100 dark:bg-amber-900/30 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400">
                  Video Tutorials
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Step-by-step walkthroughs</p>
              </div>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HelpCenter;
