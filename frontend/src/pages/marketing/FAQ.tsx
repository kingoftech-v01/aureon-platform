/**
 * FAQ Page
 * Aureon by Rhematek Solutions
 *
 * Frequently asked questions organized by category with accordion UI
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQCategory {
  name: string;
  items: FAQItem[];
}

const FAQ: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<string | null>(null);

  const toggleFaq = (key: string) => {
    setOpenIndex(openIndex === key ? null : key);
  };

  const faqCategories: FAQCategory[] = [
    {
      name: 'General',
      items: [
        {
          question: 'What is Aureon?',
          answer: 'Aureon is a comprehensive SaaS platform that automates end-to-end client financial workflows for service-based businesses. From lead capture and proposal creation to contract e-signatures, automated invoicing, payment collection via Stripe, and receipt delivery, Aureon handles the entire process in one unified platform.',
        },
        {
          question: 'Who is Aureon built for?',
          answer: 'Aureon is designed for freelancers, consultants, agencies, and service-based businesses of all sizes. Whether you are a solo designer sending a handful of invoices or a growing agency managing hundreds of client relationships, Aureon scales to fit your needs.',
        },
        {
          question: 'How do I get started?',
          answer: 'Getting started is simple: sign up for a free account, complete the onboarding wizard to configure your business profile, and you are ready to create your first contract or invoice. No credit card is required for the 14-day free trial, which gives you full access to Professional plan features.',
        },
      ],
    },
    {
      name: 'Billing & Pricing',
      items: [
        {
          question: 'What plans are available?',
          answer: 'We offer three plans: Starter (free, up to 5 clients and 10 invoices/month), Professional ($29/month or $24/month billed annually, unlimited clients and invoices), and Enterprise ($99/month or $79/month billed annually, advanced features including SSO, API access, and dedicated support). All paid plans include a 14-day free trial.',
        },
        {
          question: 'Can I change my plan at any time?',
          answer: 'Yes. You can upgrade, downgrade, or cancel your plan at any time from your account settings. Upgrades take effect immediately with prorated billing. Downgrades take effect at the end of your current billing cycle. There are no cancellation fees.',
        },
        {
          question: 'What payment methods do you accept for subscriptions?',
          answer: 'We accept all major credit and debit cards (Visa, Mastercard, American Express, Discover) for subscription payments, processed securely through Stripe. Enterprise customers can also arrange invoiced billing with net-30 terms.',
        },
        {
          question: 'Are there any hidden fees?',
          answer: 'No. Our pricing is transparent. You pay your subscription fee plus a per-transaction fee on payments processed through the platform (3% on Starter, 2% on Professional, 1.5% on Enterprise). There are no setup fees, hidden charges, or long-term commitments.',
        },
      ],
    },
    {
      name: 'Security & Privacy',
      items: [
        {
          question: 'How do you protect my data?',
          answer: 'We use AES-256 encryption at rest and TLS 1.2+ encryption in transit. All payment data is processed by Stripe (PCI DSS Level 1 certified) and never stored on our servers. We maintain SOC 2-type controls, conduct regular security audits, and support multi-factor authentication (MFA) and SSO/SAML for account access.',
        },
        {
          question: 'Are e-signatures legally binding?',
          answer: 'Yes. Our e-signature implementation complies with the ESIGN Act (United States), UETA (state-level US), and eIDAS (European Union) regulations. Every signature includes a tamper-evident record with time-stamped audit trails, signer identification, and IP address logging.',
        },
        {
          question: 'Where is my data stored?',
          answer: 'Your data is stored on secure cloud infrastructure with regional deployment options. We offer data residency configurations for organizations with specific compliance requirements. All data centers maintain ISO 27001 and SOC 2 certifications.',
        },
      ],
    },
    {
      name: 'Integrations & Features',
      items: [
        {
          question: 'What accounting software does Aureon integrate with?',
          answer: 'Aureon integrates with QuickBooks Online, Xero, and FreshBooks. Transactions, invoices, and payments sync automatically to your accounting software, eliminating double entry and ensuring your books are always up to date.',
        },
        {
          question: 'Can I accept international payments?',
          answer: 'Yes. Through our Stripe integration, Aureon supports multi-currency payments from clients in over 150 countries. You can set invoices in your client\'s preferred currency, and Aureon handles the conversion automatically. We also support region-specific tax configurations (VAT, GST, etc.).',
        },
        {
          question: 'Do you offer an API?',
          answer: 'Yes. Our REST API is available on the Enterprise plan and provides programmatic access to clients, contracts, invoices, payments, and more. We also support webhooks that trigger events when contracts are signed, payments are completed, or invoices are overdue, enabling custom automations with your existing tools.',
        },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-3">
              <div className="w-9 h-9 bg-gradient-to-br from-primary-500 via-primary-600 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">Aureon</span>
            </Link>

            <div className="flex items-center space-x-4">
              <Link to="/" className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                Back to Home
              </Link>
              <Link to="/auth/login" className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                Login
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 dark:text-white leading-tight">
            Frequently Asked{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-accent-500">
              Questions
            </span>
          </h1>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Find answers to common questions about Aureon. Can't find what you're looking for?{' '}
            <Link to="/contact" className="text-primary-500 hover:text-primary-600 font-medium">Contact our team</Link>.
          </p>
        </div>
      </section>

      {/* FAQ Categories */}
      <section className="py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto space-y-12">
          {faqCategories.map((category) => (
            <div key={category.name}>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
                <span className="w-1.5 h-6 bg-gradient-to-b from-primary-500 to-accent-500 rounded-full mr-3"></span>
                {category.name}
              </h2>

              <div className="space-y-3">
                {category.items.map((item, index) => {
                  const key = `${category.name}-${index}`;
                  return (
                    <div
                      key={key}
                      className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
                    >
                      <button
                        onClick={() => toggleFaq(key)}
                        className="w-full flex items-center justify-between px-6 py-5 text-left"
                      >
                        <span className="text-base font-medium text-gray-900 dark:text-white pr-4">
                          {item.question}
                        </span>
                        <svg
                          className={`w-5 h-5 flex-shrink-0 text-gray-500 dark:text-gray-400 transition-transform duration-200 ${
                            openIndex === key ? 'rotate-180' : ''
                          }`}
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      {openIndex === key && (
                        <div className="px-6 pb-5">
                          <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{item.answer}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
            Still have questions?
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Our team is here to help. Reach out and we'll get back to you within 24 hours.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/contact"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-2xl shadow-xl shadow-primary-500/25 transition-all duration-200"
            >
              Contact Support
            </Link>
            <Link
              to="/auth/register"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-2xl transition-colors"
            >
              Start Free Trial
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-accent-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">A</span>
              </div>
              <span className="text-lg font-bold text-gray-900 dark:text-white">Aureon</span>
            </div>

            <div className="flex items-center space-x-8 text-sm text-gray-600 dark:text-gray-400">
              <Link to="/privacy" className="hover:text-gray-900 dark:hover:text-white transition-colors">Privacy</Link>
              <Link to="/terms" className="hover:text-gray-900 dark:hover:text-white transition-colors">Terms</Link>
              <Link to="/contact" className="hover:text-gray-900 dark:hover:text-white transition-colors">Contact</Link>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-500 mt-4 md:mt-0">
              2026 Aureon by Rhematek Solutions. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default FAQ;
