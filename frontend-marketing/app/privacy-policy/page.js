"use client";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";

const page = () => {
  return (
    <PlaxLayout bg={false}>
      {/* banner */}
      <div className="mil-banner mil-banner-inner mil-dissolve">
        <div className="container">
          <div className="row align-items-center justify-content-center">
            <div className="col-xl-8">
              <div className="mil-banner-text mil-text-center">
                <div className="mil-text-m mil-mb-20">Legal</div>
                <h1 className="mil-mb-60">Privacy Policy</h1>
                <ul className="mil-breadcrumbs mil-pub-info mil-center">
                  <li>
                    <Link href="/">Home</Link>
                  </li>
                  <li>
                    <Link href="/privacy-policy/">Privacy Policy</Link>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}

      {/* content */}
      <div className="mil-p-120-90">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-8">
              <div className="mil-text-content">
                <p className="mil-text-m mil-soft mil-mb-30">
                  Last updated: January 2025
                </p>

                <h3 className="mil-mb-20">1. Introduction</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  Aureon ("we," "our," or "us") is committed to protecting your privacy.
                  This Privacy Policy explains how we collect, use, disclose, and safeguard
                  your information when you use our financial management platform.
                </p>

                <h3 className="mil-mb-20">2. Information We Collect</h3>
                <p className="mil-text-m mil-soft mil-mb-15">
                  We collect information you provide directly to us, including:
                </p>
                <ul className="mil-list-2 mil-mb-30">
                  <li>Account information (name, email, password)</li>
                  <li>Business information (company name, address, tax IDs)</li>
                  <li>Financial data (payment methods, invoices, transactions)</li>
                  <li>Client information you input into the platform</li>
                  <li>Communications with our support team</li>
                </ul>

                <h3 className="mil-mb-20">3. How We Use Your Information</h3>
                <p className="mil-text-m mil-soft mil-mb-15">
                  We use the information we collect to:
                </p>
                <ul className="mil-list-2 mil-mb-30">
                  <li>Provide, maintain, and improve our services</li>
                  <li>Process transactions and send related information</li>
                  <li>Send technical notices, updates, and security alerts</li>
                  <li>Respond to your comments, questions, and requests</li>
                  <li>Comply with legal obligations</li>
                </ul>

                <h3 className="mil-mb-20">4. Data Security</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  We implement industry-standard security measures including:
                  AES-256 encryption for data at rest, TLS 1.3 for data in transit,
                  regular security audits, and SOC 2 compliance. However, no method
                  of transmission over the Internet is 100% secure.
                </p>

                <h3 className="mil-mb-20">5. Data Retention</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  We retain your information for as long as your account is active
                  or as needed to provide you services. We will retain and use your
                  information as necessary to comply with our legal obligations,
                  resolve disputes, and enforce our agreements.
                </p>

                <h3 className="mil-mb-20">6. Your Rights</h3>
                <p className="mil-text-m mil-soft mil-mb-15">
                  Depending on your location, you may have the right to:
                </p>
                <ul className="mil-list-2 mil-mb-30">
                  <li>Access, correct, or delete your personal data</li>
                  <li>Object to or restrict certain processing</li>
                  <li>Data portability</li>
                  <li>Withdraw consent at any time</li>
                </ul>

                <h3 className="mil-mb-20">7. Third-Party Services</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  We use trusted third-party services including Stripe for payment
                  processing and cloud infrastructure providers for hosting. These
                  providers have their own privacy policies governing the use of
                  your information.
                </p>

                <h3 className="mil-mb-20">8. Cookies</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  We use cookies and similar tracking technologies to track activity
                  on our platform and hold certain information. You can instruct your
                  browser to refuse all cookies or to indicate when a cookie is being sent.
                </p>

                <h3 className="mil-mb-20">9. Changes to This Policy</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  We may update our Privacy Policy from time to time. We will notify
                  you of any changes by posting the new Privacy Policy on this page
                  and updating the "Last updated" date.
                </p>

                <h3 className="mil-mb-20">10. Contact Us</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  If you have any questions about this Privacy Policy, please contact us at:
                  <br /><br />
                  <strong>Email:</strong> privacy@aureon.io<br />
                  <strong>Address:</strong> Montreal, Quebec, Canada
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* content end */}
    </PlaxLayout>
  );
};

export default page;
