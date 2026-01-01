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
                <h1 className="mil-mb-60">Terms of Service</h1>
                <ul className="mil-breadcrumbs mil-pub-info mil-center">
                  <li>
                    <Link href="/">Home</Link>
                  </li>
                  <li>
                    <Link href="/terms-of-service/">Terms of Service</Link>
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

                <h3 className="mil-mb-20">1. Acceptance of Terms</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  By accessing or using Aureon's services, you agree to be bound by these
                  Terms of Service. If you do not agree to these terms, please do not use
                  our services.
                </p>

                <h3 className="mil-mb-20">2. Description of Service</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  Aureon provides a financial management platform that includes contract
                  generation, invoicing, payment processing, and related business automation
                  tools. We reserve the right to modify or discontinue any aspect of the
                  service at any time.
                </p>

                <h3 className="mil-mb-20">3. Account Registration</h3>
                <p className="mil-text-m mil-soft mil-mb-15">
                  To use our services, you must:
                </p>
                <ul className="mil-list-2 mil-mb-30">
                  <li>Be at least 18 years old</li>
                  <li>Provide accurate and complete registration information</li>
                  <li>Maintain the security of your account credentials</li>
                  <li>Accept responsibility for all activities under your account</li>
                </ul>

                <h3 className="mil-mb-20">4. Acceptable Use</h3>
                <p className="mil-text-m mil-soft mil-mb-15">
                  You agree not to:
                </p>
                <ul className="mil-list-2 mil-mb-30">
                  <li>Use the service for any illegal purpose</li>
                  <li>Violate any laws or regulations</li>
                  <li>Infringe on the rights of others</li>
                  <li>Attempt to gain unauthorized access to any part of the service</li>
                  <li>Interfere with or disrupt the service</li>
                  <li>Upload malicious code or content</li>
                </ul>

                <h3 className="mil-mb-20">5. Payment Terms</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  Subscription fees are billed in advance on a monthly or annual basis.
                  All fees are non-refundable except as required by law or as explicitly
                  stated in these terms. We reserve the right to change our pricing with
                  30 days notice.
                </p>

                <h3 className="mil-mb-20">6. Intellectual Property</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  The Aureon service, including all content, features, and functionality,
                  is owned by Rhematek Solutions and is protected by copyright, trademark,
                  and other intellectual property laws. You retain ownership of all data
                  you upload to the platform.
                </p>

                <h3 className="mil-mb-20">7. Data and Privacy</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  Your use of the service is also governed by our Privacy Policy. By using
                  Aureon, you consent to the collection and use of information as described
                  in our Privacy Policy.
                </p>

                <h3 className="mil-mb-20">8. Limitation of Liability</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  To the maximum extent permitted by law, Aureon shall not be liable for
                  any indirect, incidental, special, consequential, or punitive damages,
                  including loss of profits, data, or business opportunities, arising from
                  your use of the service.
                </p>

                <h3 className="mil-mb-20">9. Indemnification</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  You agree to indemnify and hold harmless Aureon and its affiliates from
                  any claims, damages, or expenses arising from your use of the service
                  or violation of these terms.
                </p>

                <h3 className="mil-mb-20">10. Termination</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  We may terminate or suspend your account at any time for violations of
                  these terms or for any other reason at our discretion. Upon termination,
                  your right to use the service will immediately cease.
                </p>

                <h3 className="mil-mb-20">11. Governing Law</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  These terms shall be governed by and construed in accordance with the
                  laws of Quebec, Canada, without regard to its conflict of law provisions.
                </p>

                <h3 className="mil-mb-20">12. Changes to Terms</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  We reserve the right to modify these terms at any time. We will provide
                  notice of significant changes by email or through the service. Your
                  continued use after changes constitutes acceptance of the new terms.
                </p>

                <h3 className="mil-mb-20">13. Contact</h3>
                <p className="mil-text-m mil-soft mil-mb-30">
                  For questions about these Terms of Service, please contact us at:
                  <br /><br />
                  <strong>Email:</strong> legal@aureon.io<br />
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
