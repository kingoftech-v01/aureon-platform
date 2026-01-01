"use client";
import Banner from "@/components/Banner";
import { CallToAction1 } from "@/components/CallToAction";
import { Testimonials2 } from "@/components/Testimonials";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";

const HomePage = () => {
  return (
    <PlaxLayout>
      {/* banner */}
      <Banner />
      {/* banner end */}

      {/* stats */}
      <div className="mil-brands mil-p-160-160">
        <div className="container">
          <h5 className="mil-text-center mil-soft mil-mb-60 mil-up">
            Trusted by businesses worldwide to automate their financial workflows
          </h5>
          <div className="row justify-content-center">
            <div className="col-6 col-md-3 mil-text-center mil-mb-30">
              <h2 className="mil-up" style={{ color: '#667eea' }}>10K+</h2>
              <p className="mil-text-m mil-soft mil-up">Contracts Created</p>
            </div>
            <div className="col-6 col-md-3 mil-text-center mil-mb-30">
              <h2 className="mil-up" style={{ color: '#667eea' }}>$50M+</h2>
              <p className="mil-text-m mil-soft mil-up">Payments Processed</p>
            </div>
            <div className="col-6 col-md-3 mil-text-center mil-mb-30">
              <h2 className="mil-up" style={{ color: '#667eea' }}>99.9%</h2>
              <p className="mil-text-m mil-soft mil-up">Uptime</p>
            </div>
            <div className="col-6 col-md-3 mil-text-center mil-mb-30">
              <h2 className="mil-up" style={{ color: '#667eea' }}>24/7</h2>
              <p className="mil-text-m mil-soft mil-up">Support</p>
            </div>
          </div>
        </div>
      </div>
      {/* stats end */}

      {/* features */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row flex-sm-row-reverse justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">End-to-End Automation</h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Aureon handles every step of your financial workflow,
                from lead capture to payment collection, all in one platform.
              </p>
              <ul className="mil-list-2 mil-type-2">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Smart Contract Generation</h5>
                    <p className="mil-text-m mil-soft">
                      Create professional contracts with dynamic templates,
                      collect e-signatures, and track milestones seamlessly.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Automated Invoicing</h5>
                    <p className="mil-text-m mil-soft">
                      Generate invoices automatically based on contract milestones
                      with support for recurring billing and multiple currencies.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <div className="mil-image-frame">
                <img src="img/home-2/2.png" alt="Aureon Automation" className="mil-up" />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}

      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-visible mil-illustration-fix mil-p-160-0">
            <div className="row align-items-end">
              <div className="mil-text-center">
                <h2 className="mil-mb-30 mil-up">
                  Collect Payments Faster <br />
                  with Stripe Integration
                </h2>
                <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                  Accept payments via credit card, bank transfer, and more.
                  Automatic retries, installment plans, and instant receipt delivery.
                </p>
              </div>
            </div>
            <div className="mil-illustration-absolute mil-up">
              <img src="img/home-2/3.png" alt="Payment Processing" />
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}

      {/* icon boxes */}
      <div className="icon-boxes mil-p-160-130">
        <div className="container">
          <div className="row">
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-with-bg mil-center mil-up">
                <img
                  src="img/home-2/icons/1.svg"
                  alt="Contract"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-up">Create Contracts</h5>
                <p className="mil-text-s mil-soft mil-up">
                  Generate professional contracts with dynamic templates,
                  conditional clauses, and customizable terms.
                </p>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-with-bg mil-center mil-up">
                <img
                  src="img/home-2/icons/2.svg"
                  alt="Invoice"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-up">Send Invoices</h5>
                <p className="mil-text-s mil-soft mil-up">
                  Automatically create and send invoices when milestones
                  are reached or on recurring schedules.
                </p>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-with-bg mil-center mil-up">
                <img
                  src="img/home-2/icons/3.svg"
                  alt="Payment"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-up">Get Paid</h5>
                <p className="mil-text-s mil-soft mil-up">
                  Collect payments via Stripe with automatic retries,
                  payment plans, and instant receipts.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* icon boxes end */}

      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-p-160-100">
            <div className="row align-items-end">
              <div className="col-xl-8 mil-mb-80-adaptive-30">
                <h2 className="mil-up">
                  Everything You Need to Scale Your Business
                </h2>
              </div>
              <div className="col-xl-4 mil-mb-80 mil-up">
                <Link
                  href="/services"
                  className="mil-btn mil-m mil-add-arrow mil-adaptive-right"
                >
                  View All Features
                </Link>
              </div>
            </div>
            <div className="row">
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/home-1/icons/1.svg"
                    alt="E-Signatures"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-30 mil-up">E-Signatures</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Legally binding digital signatures compliant
                    with eIDAS, ESIGN, and UETA regulations.
                  </p>
                </div>
              </div>
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/home-1/icons/2.svg"
                    alt="Client Portal"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-30 mil-up">Client Portal</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Branded portal where clients can view contracts,
                    invoices, make payments, and access receipts.
                  </p>
                </div>
              </div>
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/home-1/icons/3.svg"
                    alt="Analytics"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-30 mil-up">Analytics & Reporting</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Real-time dashboards, cash flow analytics,
                    and revenue recognition for compliance.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}

      {/* features */}
      <div className="mil-features mil-p-160-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Real-Time Insights & Notifications
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Stay informed with instant alerts for contract signatures,
                payment receipts, and milestone completions.
              </p>
              <ul className="mil-list-2 mil-type-2 mil-mb-60">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Activity Dashboard</h5>
                    <p className="mil-text-m mil-soft">
                      Monitor all your contracts, invoices, and payments
                      from a single, intuitive dashboard.
                    </p>
                  </div>
                </li>
              </ul>
              <div className="mil-up">
                <Link
                  href="/about"
                  className="mil-btn mil-button-transform mil-m mil-add-arrow"
                >
                  Learn More
                </Link>
              </div>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <img
                src="img/home-2/4.png"
                alt="Dashboard Analytics"
                className="mil-up"
                style={{ width: "115%" }}
              />
            </div>
          </div>
        </div>
      </div>
      {/* features end */}

      {/* features */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row flex-sm-row-reverse justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Enterprise-Grade Security
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Your data is protected with bank-level encryption,
                SOC 2 compliance, and GDPR-ready infrastructure.
              </p>
              <ul className="mil-list-2 mil-type-2">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Audit Trail</h5>
                    <p className="mil-text-m mil-soft">
                      Every action is logged with timestamps for
                      complete compliance and accountability.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Role-Based Access</h5>
                    <p className="mil-text-m mil-soft">
                      Control who can view and edit contracts, invoices,
                      and payment information with granular permissions.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <img
                src="img/home-2/5.png"
                alt="Security Features"
                className="mil-up"
                style={{ width: "100%" }}
              />
            </div>
          </div>
        </div>
      </div>
      {/* features end */}

      {/* testimonials */}
      <div className="mil-testimonials mil-p-0-160">
        <div className="container">
          <div className="row justify-content-center mil-mb-60">
            <div className="col-xl-8 mil-text-center">
              <h2 className="mil-up">What Our Customers Say</h2>
            </div>
          </div>
          <Testimonials2 />
        </div>
      </div>
      {/* testimonials end */}

      {/* call to action */}
      <CallToAction1 />
    </PlaxLayout>
  );
};
export default HomePage;
