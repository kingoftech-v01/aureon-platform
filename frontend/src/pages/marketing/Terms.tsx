/**
 * Terms of Service Page
 * Aureon by Rhematek Solutions
 *
 * Terms of service for the Aureon platform
 */

import React from 'react';
import { Link } from 'react-router-dom';

const Terms: React.FC = () => {
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

      {/* Content */}
      <section className="pt-28 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">Terms of Service</h1>
            <p className="text-gray-600 dark:text-gray-400">Last updated: March 6, 2026</p>
          </div>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-8">
            {/* Section 1 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">1. Acceptance of Terms</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                These Terms of Service ("Terms") constitute a legally binding agreement between you ("you" or "User")
                and Rhematek Solutions ("we," "us," or "Company"), the operator of the Aureon platform ("Service").
                By creating an account, accessing, or using the Service, you agree to be bound by these Terms. If you
                are using the Service on behalf of an organization, you represent and warrant that you have the authority
                to bind that organization to these Terms, and "you" shall refer to both you individually and the organization.
              </p>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mt-4">
                If you do not agree with any part of these Terms, you must not access or use the Service. We reserve
                the right to modify these Terms at any time. We will notify you of material changes via email or through
                the Service. Your continued use of the Service after such modifications constitutes your acceptance of
                the revised Terms.
              </p>
            </div>

            {/* Section 2 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">2. Description of Services</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                Aureon is a SaaS platform that provides end-to-end client financial workflow automation, including
                but not limited to:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li>Client relationship management (CRM) with contact management and lifecycle tracking.</li>
                <li>Proposal and contract generation with customizable templates and dynamic fields.</li>
                <li>Electronic signature workflows compliant with applicable laws (eIDAS, ESIGN, UETA).</li>
                <li>Automated invoicing tied to contract milestones, delivery events, or recurring schedules.</li>
                <li>Payment processing via Stripe, including credit card, bank transfer, and ACH payments.</li>
                <li>Receipt generation and delivery via email and client portal.</li>
                <li>Document management and secure storage.</li>
                <li>Analytics dashboards, reporting, and business insights.</li>
                <li>Third-party integrations with accounting, calendar, and email services.</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mt-4">
                We reserve the right to modify, suspend, or discontinue any part of the Service at any time,
                with or without notice. We will make reasonable efforts to provide advance notice of material changes.
              </p>
            </div>

            {/* Section 3 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">3. User Accounts</h2>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">3.1 Registration</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                To access the Service, you must register for an account by providing accurate, complete, and current
                information. You are responsible for maintaining the accuracy of your account information and for
                updating it as necessary.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">3.2 Account Security</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                You are responsible for safeguarding your account credentials, including passwords and API keys.
                You agree to notify us immediately of any unauthorized access to or use of your account. We
                strongly recommend enabling multi-factor authentication (MFA) for enhanced security. You are
                solely responsible for all activities that occur under your account.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">3.3 Account Termination</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                We reserve the right to suspend or terminate your account at any time if we reasonably believe
                you have violated these Terms, engaged in fraudulent activity, or if required by law. You may
                terminate your account at any time through your account settings or by contacting us.
              </p>
            </div>

            {/* Section 4 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">4. Payments and Billing</h2>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">4.1 Subscription Plans</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                The Service is offered under tiered subscription plans with varying features and limits. Plan
                details, pricing, and feature comparisons are available on our pricing page. We reserve the right
                to change pricing with 30 days' advance notice.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">4.2 Payment Terms</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                Subscription fees are billed in advance on a monthly or annual basis, depending on your selected
                billing cycle. All payments are processed through Stripe. By providing payment information, you
                authorize us to charge the applicable fees to your payment method. All fees are non-refundable
                unless otherwise specified or required by applicable law.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">4.3 Transaction Fees</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                Payment processing through the Service is subject to transaction fees that vary by plan tier.
                These fees are deducted from each transaction processed on your behalf. Current fee rates are
                displayed on your plan details page.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">4.4 Taxes</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                All fees are exclusive of applicable taxes unless stated otherwise. You are responsible for
                paying all taxes, levies, and duties associated with your use of the Service, except for taxes
                based on our net income.
              </p>
            </div>

            {/* Section 5 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">5. Intellectual Property</h2>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">5.1 Our Intellectual Property</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                The Service, including all software, designs, text, graphics, logos, trademarks, and other
                content, is owned by or licensed to Rhematek Solutions and is protected by intellectual property
                laws. You are granted a limited, non-exclusive, non-transferable, revocable license to access
                and use the Service in accordance with these Terms.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">5.2 Your Content</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                You retain all ownership rights to the content you create, upload, or transmit through the
                Service ("Your Content"), including contracts, invoices, documents, and client data. By using
                the Service, you grant us a limited, non-exclusive license to store, process, display, and
                transmit Your Content solely for the purpose of providing the Service. This license terminates
                when you delete Your Content or close your account.
              </p>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">5.3 Feedback</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                If you provide us with feedback, suggestions, or ideas regarding the Service, you grant us a
                perpetual, irrevocable, worldwide, royalty-free license to use, modify, and incorporate such
                feedback into the Service without any obligation to you.
              </p>
            </div>

            {/* Section 6 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">6. Acceptable Use</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                You agree not to use the Service to:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li>Violate any applicable law, regulation, or third-party right.</li>
                <li>Transmit any content that is unlawful, harmful, threatening, defamatory, or otherwise objectionable.</li>
                <li>Engage in fraud, money laundering, or other financial crimes.</li>
                <li>Interfere with or disrupt the Service, servers, or networks connected to the Service.</li>
                <li>Attempt to gain unauthorized access to the Service, other accounts, or computer systems.</li>
                <li>Use the Service for any purpose other than its intended business use.</li>
                <li>Reverse engineer, decompile, or disassemble any part of the Service.</li>
                <li>Resell, sublicense, or redistribute the Service without our written consent.</li>
              </ul>
            </div>

            {/* Section 7 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">7. Limitation of Liability</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li>THE SERVICE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS WITHOUT WARRANTIES OF ANY KIND,
                    WHETHER EXPRESS, IMPLIED, OR STATUTORY, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
                    PARTICULAR PURPOSE, AND NON-INFRINGEMENT.</li>
                <li>WE SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE
                    DAMAGES, INCLUDING LOSS OF PROFITS, REVENUE, DATA, OR BUSINESS OPPORTUNITIES, ARISING OUT
                    OF OR RELATING TO YOUR USE OF THE SERVICE.</li>
                <li>OUR TOTAL AGGREGATE LIABILITY FOR ALL CLAIMS RELATED TO THE SERVICE SHALL NOT EXCEED THE
                    AMOUNT YOU PAID TO US IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mt-4">
                Some jurisdictions do not allow the exclusion of certain warranties or limitation of liability,
                so the above limitations may not apply to you. In such cases, our liability is limited to the
                fullest extent permitted by law.
              </p>
            </div>

            {/* Section 8 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">8. Indemnification</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                You agree to indemnify, defend, and hold harmless Rhematek Solutions, its officers, directors,
                employees, and agents from and against any and all claims, damages, losses, liabilities, costs,
                and expenses (including reasonable attorneys' fees) arising from or related to: (a) your use of
                the Service; (b) your violation of these Terms; (c) your violation of any applicable law or
                regulation; or (d) Your Content or any data you transmit through the Service.
              </p>
            </div>

            {/* Section 9 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">9. Dispute Resolution</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                Any dispute arising out of or relating to these Terms or the Service shall first be attempted
                to be resolved through good-faith negotiation between the parties. If the dispute cannot be
                resolved through negotiation within 30 days, it shall be submitted to binding arbitration in
                accordance with the rules of the American Arbitration Association (AAA), conducted in San Francisco,
                California, USA. The arbitrator's decision shall be final and binding. Notwithstanding the foregoing,
                either party may seek injunctive or equitable relief in a court of competent jurisdiction.
              </p>
            </div>

            {/* Section 10 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">10. General Provisions</h2>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li><strong>Governing law:</strong> These Terms are governed by the laws of the State of California,
                    without regard to its conflict of laws principles.</li>
                <li><strong>Severability:</strong> If any provision of these Terms is found to be unenforceable,
                    the remaining provisions shall continue in full force and effect.</li>
                <li><strong>Waiver:</strong> Our failure to enforce any right or provision of these Terms shall not
                    constitute a waiver of that right or provision.</li>
                <li><strong>Entire agreement:</strong> These Terms, together with the Privacy Policy, constitute the
                    entire agreement between you and us regarding the Service.</li>
                <li><strong>Assignment:</strong> You may not assign or transfer your rights or obligations under
                    these Terms without our prior written consent. We may assign our rights and obligations without restriction.</li>
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">11. Contact Information</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                If you have any questions about these Terms, please contact us:
              </p>
              <div className="mt-4 p-6 bg-gray-50 dark:bg-gray-800 rounded-xl">
                <p className="text-gray-700 dark:text-gray-300 font-medium">Rhematek Solutions</p>
                <p className="text-gray-600 dark:text-gray-400">Email: legal@aureon.io</p>
                <p className="text-gray-600 dark:text-gray-400">Address: 123 Finance Drive, Suite 400, San Francisco, CA 94105</p>
              </div>
            </div>
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
              <Link to="/contact" className="hover:text-gray-900 dark:hover:text-white transition-colors">Contact</Link>
              <Link to="/about" className="hover:text-gray-900 dark:hover:text-white transition-colors">About</Link>
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

export default Terms;
