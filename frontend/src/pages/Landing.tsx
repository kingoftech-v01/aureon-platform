/**
 * Landing Page
 * Aureon by Rhematek Solutions
 *
 * Marketing landing page with features, pricing, and call-to-action
 */

import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';

const Landing: React.FC = () => {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);
  const [newsletterEmail, setNewsletterEmail] = useState('');
  const [newsletterSubmitted, setNewsletterSubmitted] = useState(false);

  const handleSmoothScroll = useCallback((e: React.MouseEvent<HTMLAnchorElement>, targetId: string) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    const el = document.getElementById(targetId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  const handleNewsletterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newsletterEmail.trim()) {
      setNewsletterSubmitted(true);
      setNewsletterEmail('');
      setTimeout(() => setNewsletterSubmitted(false), 5000);
    }
  };

  const features = [
    {
      title: 'Client Management',
      description: 'Organize contacts, track interactions, and nurture relationships with a powerful CRM built for service businesses.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      ),
    },
    {
      title: 'Smart Contracts',
      description: 'Create professional contracts with dynamic templates, e-signatures, and automated milestone tracking.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
      ),
    },
    {
      title: 'Automated Invoicing',
      description: 'Send professional invoices automatically, track payments, and get paid faster with Stripe integration.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
        </svg>
      ),
    },
    {
      title: 'Payment Processing',
      description: 'Accept payments via credit card, bank transfer, or ACH with secure Stripe-powered checkout.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
        </svg>
      ),
    },
    {
      title: 'Analytics & Reports',
      description: 'Get real-time insights into revenue, cash flow, and client performance with beautiful dashboards.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
        </svg>
      ),
    },
    {
      title: 'Document Vault',
      description: 'Store and organize all your contracts, receipts, and business documents securely in one place.',
      icon: (
        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
        </svg>
      ),
    },
  ];

  const howItWorksSteps = [
    {
      step: 1,
      title: 'Create Contract',
      description: 'Choose from professional templates, customize terms and milestones, and send for e-signature in minutes.',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
      ),
    },
    {
      step: 2,
      title: 'Auto-Invoice',
      description: 'Invoices are automatically generated when milestones are completed or on your billing schedule.',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
        </svg>
      ),
    },
    {
      step: 3,
      title: 'Get Paid',
      description: 'Clients pay securely via Stripe. Receipts are sent automatically and funds hit your account fast.',
      icon: (
        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  const socialProofStats = [
    { value: '10,000+', label: 'Businesses' },
    { value: '$50M+', label: 'Processed' },
    { value: '99.9%', label: 'Uptime' },
    { value: '150+', label: 'Countries' },
  ];

  const pricingPlans = [
    {
      name: 'Starter',
      description: 'Perfect for freelancers just getting started',
      monthlyPrice: 0,
      yearlyPrice: 0,
      features: [
        'Up to 5 clients',
        '10 invoices per month',
        'Basic contract templates',
        'Email support',
        'Payment processing (3% fee)',
      ],
      cta: 'Start Free',
      popular: false,
    },
    {
      name: 'Professional',
      description: 'For growing businesses and agencies',
      monthlyPrice: 29,
      yearlyPrice: 24,
      features: [
        'Unlimited clients',
        'Unlimited invoices',
        'Custom contract templates',
        'E-signature support',
        'Priority support',
        'Payment processing (2% fee)',
        'Analytics dashboard',
        'Document vault',
      ],
      cta: 'Start Trial',
      popular: true,
    },
    {
      name: 'Enterprise',
      description: 'For large teams with custom needs',
      monthlyPrice: 99,
      yearlyPrice: 79,
      features: [
        'Everything in Professional',
        'Team collaboration',
        'Custom branding',
        'API access',
        'Dedicated account manager',
        'Payment processing (1.5% fee)',
        'Advanced analytics',
        'SSO & SAML',
        'Custom integrations',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  const testimonials = [
    {
      quote: "Aureon has transformed how I manage my freelance business. Invoicing used to take hours, now it's automatic.",
      author: 'Sarah Chen',
      role: 'UX Designer',
      avatar: 'SC',
    },
    {
      quote: "The contract management feature alone is worth it. My clients love the professional e-signature experience.",
      author: 'Marcus Johnson',
      role: 'Marketing Consultant',
      avatar: 'MJ',
    },
    {
      quote: "Finally, a platform that understands what service businesses need. The analytics help me make smarter decisions.",
      author: 'Emily Rodriguez',
      role: 'Business Coach',
      avatar: 'ER',
    },
  ];

  const faqItems = [
    {
      question: 'How does the 14-day free trial work?',
      answer: 'You get full access to all Professional plan features for 14 days, no credit card required. At the end of the trial, you can choose a plan that fits your needs or continue with the free Starter plan.',
    },
    {
      question: 'Is my financial data secure?',
      answer: 'Absolutely. We use AES-256 encryption at rest and TLS 1.2+ in transit. All payment processing is handled by Stripe, which is PCI DSS Level 1 certified. We also support SSO/SAML and maintain SOC 2-type controls.',
    },
    {
      question: 'What payment methods do you support?',
      answer: 'Through our Stripe integration, you can accept credit cards, debit cards, ACH bank transfers, and other popular payment methods. We support multi-currency transactions across 150+ countries.',
    },
    {
      question: 'Can I integrate Aureon with my accounting software?',
      answer: 'Yes. Aureon integrates with QuickBooks, Xero, and other popular accounting tools. We also offer webhooks and a REST API for custom integrations with your existing tech stack.',
    },
    {
      question: 'How do e-signatures work?',
      answer: 'Our e-signature system is compliant with eIDAS, ESIGN, and UETA regulations. Clients receive a secure link to review and sign contracts digitally. All signatures are tamper-evident with time-stamped audit trails.',
    },
    {
      question: 'Can I cancel or change my plan at any time?',
      answer: 'Yes, you can upgrade, downgrade, or cancel your plan at any time from your account settings. If you downgrade, the change takes effect at the end of your current billing cycle. No cancellation fees.',
    },
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950" style={{ scrollBehavior: 'smooth' }}>
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 bg-gradient-to-br from-primary-500 via-primary-600 to-accent-500 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">Aureon</span>
            </div>

            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" onClick={(e) => handleSmoothScroll(e, 'features')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Features</a>
              <a href="#how-it-works" onClick={(e) => handleSmoothScroll(e, 'how-it-works')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">How It Works</a>
              <a href="#pricing" onClick={(e) => handleSmoothScroll(e, 'pricing')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Pricing</a>
              <a href="#testimonials" onClick={(e) => handleSmoothScroll(e, 'testimonials')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Testimonials</a>
            </div>

            <div className="hidden md:flex items-center space-x-4">
              <Link to="/auth/login" className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors">
                Sign In
              </Link>
              <Link
                to="/auth/register"
                className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-xl shadow-lg shadow-primary-500/25 transition-all duration-200"
              >
                Get Started Free
              </Link>
            </div>

            {/* Mobile Hamburger Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>

          {/* Mobile Menu Dropdown */}
          {mobileMenuOpen && (
            <div className="md:hidden pb-4 border-t border-gray-200 dark:border-gray-800">
              <div className="flex flex-col space-y-3 pt-4">
                <a href="#features" onClick={(e) => handleSmoothScroll(e, 'features')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors px-2 py-1">Features</a>
                <a href="#how-it-works" onClick={(e) => handleSmoothScroll(e, 'how-it-works')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors px-2 py-1">How It Works</a>
                <a href="#pricing" onClick={(e) => handleSmoothScroll(e, 'pricing')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors px-2 py-1">Pricing</a>
                <a href="#testimonials" onClick={(e) => handleSmoothScroll(e, 'testimonials')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors px-2 py-1">Testimonials</a>
                <a href="#faq" onClick={(e) => handleSmoothScroll(e, 'faq')} className="text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors px-2 py-1">FAQ</a>
                <div className="pt-2 border-t border-gray-200 dark:border-gray-800 flex flex-col space-y-3">
                  <Link to="/auth/login" className="text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors px-2 py-1">
                    Sign In
                  </Link>
                  <Link
                    to="/auth/register"
                    className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-xl shadow-lg shadow-primary-500/25 transition-all duration-200 text-center"
                  >
                    Get Started Free
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center px-4 py-2 mb-6 text-sm font-medium text-primary-700 dark:text-primary-300 bg-primary-50 dark:bg-primary-900/20 rounded-full border border-primary-100 dark:border-primary-800">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
              Now with AI-powered contract generation
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 dark:text-white leading-tight">
              Run your service business{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-accent-500">
                with confidence
              </span>
            </h1>

            <p className="mt-6 text-lg sm:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              From lead to payment, Aureon automates your entire client workflow. Create contracts, send invoices, and get paid faster with one unified platform.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/auth/register"
                className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-2xl shadow-xl shadow-primary-500/25 transition-all duration-200 hover:shadow-primary-500/40"
              >
                Start Free Trial
              </Link>
              <a
                href="#features"
                onClick={(e) => handleSmoothScroll(e, 'features')}
                className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-2xl transition-colors flex items-center justify-center"
              >
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Watch Demo
              </a>
            </div>

            <p className="mt-6 text-sm text-gray-500 dark:text-gray-400">
              No credit card required. 14-day free trial.
            </p>
          </div>

          {/* Dashboard Preview */}
          <div className="mt-16 relative">
            <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent dark:from-gray-950 pointer-events-none z-10"></div>
            <div className="bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 rounded-3xl p-2 shadow-2xl">
              <div className="bg-white dark:bg-gray-900 rounded-2xl overflow-hidden">
                <div className="flex items-center px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex space-x-2">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  </div>
                </div>
                <div className="aspect-[16/9] bg-gradient-to-br from-primary-50 to-accent-50 dark:from-gray-800 dark:to-gray-900 flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-20 h-20 bg-primary-100 dark:bg-primary-900/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <svg className="w-10 h-10 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v2a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 12a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1h-4a1 1 0 01-1-1v-7z" />
                      </svg>
                    </div>
                    <p className="text-lg font-medium text-gray-600 dark:text-gray-400">Dashboard Preview</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof Metrics Bar */}
      <section className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900/50 border-y border-gray-200/50 dark:border-gray-800/50">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {socialProofStats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl sm:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-accent-500">
                  {stat.value}
                </p>
                <p className="mt-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              How it works
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Get from contract to payment in three simple steps.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Connecting line (hidden on mobile) */}
            <div className="hidden md:block absolute top-16 left-[20%] right-[20%] h-0.5 bg-gradient-to-r from-primary-200 via-primary-300 to-accent-200 dark:from-primary-800 dark:via-primary-700 dark:to-accent-800"></div>

            {howItWorksSteps.map((step) => (
              <div key={step.step} className="relative text-center">
                <div className="relative z-10 mx-auto w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl flex items-center justify-center text-white shadow-lg shadow-primary-500/25 mb-6">
                  {step.icon}
                </div>
                <div className="absolute -top-2 -right-2 md:right-auto md:left-1/2 md:ml-4 md:-top-1 w-7 h-7 bg-accent-500 rounded-full flex items-center justify-center text-white text-xs font-bold shadow-md z-20">
                  {step.step}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3">
                  {step.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 max-w-xs mx-auto">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              Everything you need to grow your business
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Powerful features designed for freelancers, agencies, and service-based businesses.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-700 transition-all duration-200 hover:shadow-xl hover:shadow-primary-500/5"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-50 dark:from-primary-900/30 dark:to-primary-800/20 rounded-xl flex items-center justify-center text-primary-600 dark:text-primary-400 mb-4 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              Simple, transparent pricing
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Choose the plan that fits your business. All plans include a 14-day free trial.
            </p>

            {/* Billing Toggle */}
            <div className="mt-8 inline-flex items-center p-1 bg-gray-100 dark:bg-gray-800 rounded-xl">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                  billingPeriod === 'monthly'
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod('yearly')}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                  billingPeriod === 'yearly'
                    ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Yearly
                <span className="ml-1 text-xs text-green-600 dark:text-green-400">Save 20%</span>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingPlans.map((plan) => (
              <div
                key={plan.name}
                className={`relative p-6 rounded-2xl border ${
                  plan.popular
                    ? 'bg-gradient-to-br from-primary-500 to-primary-600 border-primary-500 shadow-xl shadow-primary-500/25'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-3 py-1 text-xs font-semibold text-primary-700 bg-white rounded-full shadow-lg">
                      Most Popular
                    </span>
                  </div>
                )}

                <h3 className={`text-lg font-semibold ${plan.popular ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
                  {plan.name}
                </h3>
                <p className={`mt-1 text-sm ${plan.popular ? 'text-primary-100' : 'text-gray-600 dark:text-gray-400'}`}>
                  {plan.description}
                </p>

                <div className="mt-4">
                  <span className={`text-4xl font-bold ${plan.popular ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
                    ${billingPeriod === 'monthly' ? plan.monthlyPrice : plan.yearlyPrice}
                  </span>
                  <span className={`text-sm ${plan.popular ? 'text-primary-100' : 'text-gray-600 dark:text-gray-400'}`}>
                    /month
                  </span>
                </div>

                <ul className="mt-6 space-y-3">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start">
                      <svg
                        className={`w-5 h-5 mr-2 flex-shrink-0 ${plan.popular ? 'text-primary-100' : 'text-green-500'}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className={`text-sm ${plan.popular ? 'text-primary-100' : 'text-gray-600 dark:text-gray-400'}`}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <Link
                  to="/auth/register"
                  className={`mt-8 block w-full py-3 px-4 text-center text-sm font-semibold rounded-xl transition-all ${
                    plan.popular
                      ? 'bg-white text-primary-600 hover:bg-primary-50 shadow-lg'
                      : 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-100'
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              Loved by thousands of businesses
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              See what our customers have to say about Aureon.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial) => (
              <div
                key={testimonial.author}
                className="p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  ))}
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-6">"{testimonial.quote}"</p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                    {testimonial.avatar}
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">{testimonial.author}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{testimonial.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            Ready to streamline your business?
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Join thousands of professionals who trust Aureon to manage their client relationships.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/auth/register"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-2xl shadow-xl shadow-primary-500/25 transition-all duration-200"
            >
              Start Your Free Trial
            </Link>
            <Link
              to="/auth/login"
              className="w-full sm:w-auto px-8 py-4 text-base font-semibold text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Already have an account? Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              Frequently asked questions
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Everything you need to know about Aureon. Can't find the answer you're looking for?{' '}
              <Link to="/contact" className="text-primary-500 hover:text-primary-600 font-medium">Contact us</Link>.
            </p>
          </div>

          <div className="space-y-4">
            {faqItems.map((item, index) => (
              <div
                key={index}
                className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaqIndex(openFaqIndex === index ? null : index)}
                  className="w-full flex items-center justify-between px-6 py-5 text-left"
                >
                  <span className="text-base font-medium text-gray-900 dark:text-white pr-4">
                    {item.question}
                  </span>
                  <svg
                    className={`w-5 h-5 flex-shrink-0 text-gray-500 dark:text-gray-400 transition-transform duration-200 ${
                      openFaqIndex === index ? 'rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openFaqIndex === index && (
                  <div className="px-6 pb-5">
                    <p className="text-gray-600 dark:text-gray-400">{item.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            {/* Brand & Newsletter */}
            <div className="md:col-span-2">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-accent-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">A</span>
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">Aureon</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 max-w-md">
                Automate your entire client workflow from lead to payment. Built for freelancers, agencies, and service-based businesses.
              </p>

              {/* Newsletter Signup */}
              <div className="max-w-sm">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Stay updated
                </p>
                {newsletterSubmitted ? (
                  <p className="text-sm text-green-600 dark:text-green-400 font-medium">
                    Thanks for subscribing! Check your inbox.
                  </p>
                ) : (
                  <form onSubmit={handleNewsletterSubmit} className="flex gap-2">
                    <input
                      type="email"
                      required
                      placeholder="Enter your email"
                      value={newsletterEmail}
                      onChange={(e) => setNewsletterEmail(e.target.value)}
                      className="flex-1 px-4 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none text-gray-900 dark:text-white placeholder-gray-400"
                    />
                    <button
                      type="submit"
                      className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 rounded-xl transition-all duration-200 whitespace-nowrap"
                    >
                      Subscribe
                    </button>
                  </form>
                )}
              </div>
            </div>

            {/* Product Links */}
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" onClick={(e) => handleSmoothScroll(e, 'features')} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" onClick={(e) => handleSmoothScroll(e, 'pricing')} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#testimonials" onClick={(e) => handleSmoothScroll(e, 'testimonials')} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Testimonials</a></li>
                <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, 'faq')} className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">FAQ</a></li>
              </ul>
            </div>

            {/* Company Links */}
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><Link to="/about" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">About</Link></li>
                <li><Link to="/contact" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Contact</Link></li>
                <li><Link to="/privacy" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Privacy Policy</Link></li>
                <li><Link to="/terms" className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Terms of Service</Link></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-gray-200 dark:border-gray-800 flex flex-col md:flex-row items-center justify-between">
            <p className="text-sm text-gray-500 dark:text-gray-500">
              2026 Aureon by Rhematek Solutions. All rights reserved.
            </p>
            <div className="flex items-center space-x-6 mt-4 md:mt-0">
              <Link to="/privacy" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Privacy</Link>
              <Link to="/terms" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Terms</Link>
              <Link to="/contact" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">Support</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
