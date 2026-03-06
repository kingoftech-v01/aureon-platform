/**
 * Privacy Policy Page
 * Aureon by Rhematek Solutions
 *
 * Privacy policy for the Aureon platform
 */

import React from 'react';
import { Link } from 'react-router-dom';

const Privacy: React.FC = () => {
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
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">Privacy Policy</h1>
            <p className="text-gray-600 dark:text-gray-400">Last updated: March 6, 2026</p>
          </div>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-8">
            {/* Introduction */}
            <div>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                Aureon, operated by Rhematek Solutions ("we," "us," or "our"), is committed to protecting and
                respecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard
                your information when you use our SaaS platform and related services (collectively, the "Service").
                Please read this policy carefully. By accessing or using the Service, you acknowledge that you have
                read, understood, and agree to be bound by all the terms of this Privacy Policy.
              </p>
            </div>

            {/* Section 1 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">1. Information We Collect</h2>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">1.1 Information You Provide</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                We collect information you provide directly when creating an account, using our services, or
                communicating with us. This may include:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li>Account information: name, email address, password, company name, and billing address.</li>
                <li>Profile information: job title, phone number, and profile photo.</li>
                <li>Financial information: bank account details, tax identification numbers, and payment method
                    information processed through our payment partner, Stripe.</li>
                <li>Content: contracts, proposals, invoices, receipts, documents, and communications you create,
                    upload, or transmit through the Service.</li>
                <li>Communications: messages you send to us via email, support tickets, or contact forms.</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-2">1.2 Information Collected Automatically</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                When you access or use the Service, we automatically collect certain information, including:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li>Device information: IP address, browser type and version, operating system, and device identifiers.</li>
                <li>Usage data: pages visited, features used, time spent on pages, click patterns, and referral URLs.</li>
                <li>Log data: server logs, error reports, and performance metrics.</li>
                <li>Cookies and similar technologies: session cookies, persistent cookies, and web beacons as described
                    in Section 6.</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-2">1.3 Information from Third Parties</h3>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                We may receive information about you from third-party services you integrate with Aureon, such as
                accounting software (QuickBooks, Xero), calendar services, email providers, and payment processors.
                The information received depends on the integration and your third-party account settings.
              </p>
            </div>

            {/* Section 2 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">2. How We Use Your Information</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                We use the information we collect for the following purposes:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li><strong>Service delivery:</strong> To create and manage your account, process transactions,
                    generate contracts and invoices, facilitate e-signatures, and provide customer support.</li>
                <li><strong>Payment processing:</strong> To process payments, manage subscriptions, handle refunds,
                    and comply with financial regulations through our integration with Stripe.</li>
                <li><strong>Communication:</strong> To send transactional emails (invoices, receipts, contract
                    notifications), service updates, security alerts, and marketing communications (with your consent).</li>
                <li><strong>Improvement:</strong> To analyze usage patterns, diagnose technical issues, develop new
                    features, and improve the overall user experience.</li>
                <li><strong>Security:</strong> To detect, prevent, and address fraud, unauthorized access, and other
                    illegal activities.</li>
                <li><strong>Legal compliance:</strong> To comply with applicable laws, regulations, legal processes,
                    and governmental requests.</li>
              </ul>
            </div>

            {/* Section 3 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">3. Information Sharing and Disclosure</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                We do not sell your personal information. We may share your information in the following circumstances:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li><strong>Service providers:</strong> With trusted third-party vendors who assist us in operating our
                    platform, including cloud hosting providers, payment processors (Stripe), email delivery services,
                    and analytics tools. These providers are contractually obligated to protect your data.</li>
                <li><strong>Business transfers:</strong> In connection with a merger, acquisition, reorganization, or
                    sale of assets, your information may be transferred as a business asset. We will notify you of any
                    such change.</li>
                <li><strong>Legal requirements:</strong> When required by law, regulation, subpoena, court order, or
                    other legal process, or when we believe disclosure is necessary to protect our rights, your safety,
                    or the safety of others.</li>
                <li><strong>With your consent:</strong> When you explicitly authorize us to share your information with
                    a specific third party.</li>
                <li><strong>Client interactions:</strong> When you send contracts, invoices, or receipts to your clients
                    through the Service, the relevant information is shared with those recipients.</li>
              </ul>
            </div>

            {/* Section 4 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">4. Data Security</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                We implement industry-standard security measures to protect your information:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li><strong>Encryption:</strong> All data is encrypted at rest using AES-256 and in transit using TLS 1.2 or higher.</li>
                <li><strong>Authentication:</strong> We support OAuth2, SAML SSO, and multi-factor authentication (MFA)
                    for account access.</li>
                <li><strong>Access controls:</strong> Role-based access control (RBAC) ensures that only authorized
                    personnel can access sensitive data. Internal access is logged and audited.</li>
                <li><strong>Infrastructure:</strong> Our platform is hosted on secure cloud infrastructure with regular
                    security audits, vulnerability scanning, and penetration testing.</li>
                <li><strong>Compliance:</strong> We maintain SOC 2-type controls and follow secure development lifecycle
                    practices.</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mt-4">
                While we strive to protect your personal information, no method of electronic storage or transmission
                over the Internet is 100% secure. We cannot guarantee absolute security but are committed to promptly
                addressing any security incidents.
              </p>
            </div>

            {/* Section 5 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">5. Your Rights and Choices</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                Depending on your jurisdiction, you may have the following rights:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li><strong>Access:</strong> Request a copy of the personal information we hold about you.</li>
                <li><strong>Correction:</strong> Request correction of inaccurate or incomplete personal information.</li>
                <li><strong>Deletion:</strong> Request deletion of your personal information, subject to legal retention requirements.</li>
                <li><strong>Portability:</strong> Request your data in a structured, commonly used, machine-readable format.</li>
                <li><strong>Objection:</strong> Object to processing of your personal information for certain purposes.</li>
                <li><strong>Restriction:</strong> Request restriction of processing in certain circumstances.</li>
                <li><strong>Withdraw consent:</strong> Where processing is based on consent, you may withdraw it at any time.</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mt-4">
                For GDPR (European Union), CCPA (California), and similar regulatory frameworks, we act as a data
                processor for your client data and as a data controller for your account data. To exercise any of
                these rights, please contact us at privacy@aureon.io.
              </p>
            </div>

            {/* Section 6 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">6. Cookies and Tracking Technologies</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-4">
                We use cookies and similar tracking technologies to enhance your experience:
              </p>
              <ul className="list-disc pl-6 space-y-2 text-gray-600 dark:text-gray-400">
                <li><strong>Essential cookies:</strong> Required for the Service to function properly (authentication,
                    security, session management).</li>
                <li><strong>Analytics cookies:</strong> Help us understand how users interact with the Service to improve
                    functionality and user experience.</li>
                <li><strong>Preference cookies:</strong> Remember your settings and preferences (language, theme,
                    dashboard layout).</li>
              </ul>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed mt-4">
                You can manage cookie preferences through your browser settings. Disabling certain cookies may limit
                your ability to use some features of the Service.
              </p>
            </div>

            {/* Section 7 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">7. Data Retention</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                We retain your personal information for as long as your account is active or as needed to provide
                the Service. We also retain information as necessary to comply with legal obligations (including
                financial record-keeping requirements), resolve disputes, enforce agreements, and support business
                operations. When you delete your account, we will delete or anonymize your personal information
                within 90 days, except where retention is required by law or for legitimate business purposes.
              </p>
            </div>

            {/* Section 8 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">8. International Data Transfers</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                Your information may be transferred to and processed in countries other than your country of residence.
                We ensure appropriate safeguards are in place for international transfers, including Standard
                Contractual Clauses (SCCs) approved by the European Commission or other legally recognized transfer
                mechanisms. We deploy infrastructure in multiple regions to minimize data transfer where possible.
              </p>
            </div>

            {/* Section 9 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">9. Children's Privacy</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                The Service is not directed to individuals under the age of 18. We do not knowingly collect personal
                information from children. If we become aware that we have inadvertently collected personal information
                from a child under 18, we will take steps to delete such information promptly.
              </p>
            </div>

            {/* Section 10 */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">10. Changes to This Policy</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                We may update this Privacy Policy from time to time to reflect changes in our practices, technology,
                legal requirements, or other factors. We will notify you of material changes by posting the updated
                policy on our website and, where appropriate, by email. Your continued use of the Service after any
                changes constitutes your acceptance of the updated Privacy Policy.
              </p>
            </div>

            {/* Contact */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">11. Contact Us</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                If you have any questions or concerns about this Privacy Policy or our data practices, please contact us:
              </p>
              <div className="mt-4 p-6 bg-gray-50 dark:bg-gray-800 rounded-xl">
                <p className="text-gray-700 dark:text-gray-300 font-medium">Rhematek Solutions</p>
                <p className="text-gray-600 dark:text-gray-400">Email: privacy@aureon.io</p>
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
              <Link to="/terms" className="hover:text-gray-900 dark:hover:text-white transition-colors">Terms</Link>
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

export default Privacy;
