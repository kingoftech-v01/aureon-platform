"use client";
import { CallToAction2 } from "@/components/CallToAction";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
import { useState } from "react";

const faqData = [
  {
    category: "General",
    questions: [
      {
        q: "What is Aureon?",
        a: "Aureon is a comprehensive financial management platform that automates end-to-end client financial workflows including contract generation, invoicing, payment collection, and real-time dashboards."
      },
      {
        q: "How do I get started with Aureon?",
        a: "Simply sign up for a free trial on our website. You'll get immediate access to all features and can start managing your financial workflows right away."
      },
      {
        q: "Is Aureon suitable for my business size?",
        a: "Aureon is designed for businesses of all sizes, from freelancers to growing enterprises. Our flexible pricing plans adapt to your needs."
      }
    ]
  },
  {
    category: "Billing & Payments",
    questions: [
      {
        q: "What payment methods do you accept?",
        a: "We accept all major credit cards, debit cards, and bank transfers through our secure Stripe integration."
      },
      {
        q: "Can I change my plan at any time?",
        a: "Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, and we'll prorate any differences."
      },
      {
        q: "Is there a free trial?",
        a: "Yes, we offer a 14-day free trial with full access to all features. No credit card required to start."
      }
    ]
  },
  {
    category: "Security & Privacy",
    questions: [
      {
        q: "How secure is my data?",
        a: "We use bank-level encryption (AES-256) for all data at rest and TLS 1.3 for data in transit. Our infrastructure is SOC 2 compliant."
      },
      {
        q: "Where is my data stored?",
        a: "Your data is stored in secure, geographically distributed data centers with automatic backups and disaster recovery."
      },
      {
        q: "Do you share my data with third parties?",
        a: "Never. Your data is yours. We don't sell or share your information with any third parties."
      }
    ]
  },
  {
    category: "Features & Integration",
    questions: [
      {
        q: "Can I integrate Aureon with my existing tools?",
        a: "Yes, Aureon integrates with popular tools including QuickBooks, Xero, Stripe, Google Calendar, and many more via our API and webhooks."
      },
      {
        q: "Does Aureon support multiple currencies?",
        a: "Yes, we support over 135 currencies with automatic conversion and region-specific tax handling."
      },
      {
        q: "Can I customize contracts and invoices?",
        a: "Absolutely. You can fully customize templates with your branding, terms, and dynamic fields for personalized client experiences."
      }
    ]
  }
];

const FAQItem = ({ question, answer, isOpen, onClick }) => {
  return (
    <div className="mil-accordion-item mil-up">
      <div
        className={`mil-accordion-header ${isOpen ? 'mil-active' : ''}`}
        onClick={onClick}
        style={{ cursor: 'pointer' }}
      >
        <h5>{question}</h5>
        <span className="mil-accordion-icon">
          {isOpen ? '-' : '+'}
        </span>
      </div>
      {isOpen && (
        <div className="mil-accordion-content">
          <p className="mil-text-m mil-soft">{answer}</p>
        </div>
      )}
    </div>
  );
};

const page = () => {
  const [openItems, setOpenItems] = useState({});

  const toggleItem = (categoryIndex, questionIndex) => {
    const key = `${categoryIndex}-${questionIndex}`;
    setOpenItems(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  return (
    <PlaxLayout bg={false}>
      {/* banner */}
      <div className="mil-banner mil-banner-inner mil-dissolve">
        <div className="container">
          <div className="row align-items-center justify-content-center">
            <div className="col-xl-8">
              <div className="mil-banner-text mil-text-center">
                <div className="mil-text-m mil-mb-20">FAQ</div>
                <h1 className="mil-mb-60">
                  Frequently Asked Questions
                </h1>
                <ul className="mil-breadcrumbs mil-pub-info mil-center">
                  <li>
                    <Link href="/">Home</Link>
                  </li>
                  <li>
                    <Link href="/faq/">FAQ</Link>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}

      {/* FAQ content */}
      <div className="mil-p-120-90">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-10">
              {faqData.map((category, categoryIndex) => (
                <div key={categoryIndex} className="mil-mb-60">
                  <h3 className="mil-mb-30 mil-up">{category.category}</h3>
                  <div className="mil-accordion">
                    {category.questions.map((item, questionIndex) => (
                      <FAQItem
                        key={questionIndex}
                        question={item.q}
                        answer={item.a}
                        isOpen={openItems[`${categoryIndex}-${questionIndex}`]}
                        onClick={() => toggleItem(categoryIndex, questionIndex)}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      {/* FAQ content end */}

      {/* CTA */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-p-160-100">
            <div className="row justify-content-center mil-text-center">
              <div className="col-xl-8">
                <h2 className="mil-mb-30 mil-up">Still have questions?</h2>
                <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                  Our support team is here to help. Reach out to us anytime.
                </p>
                <Link href="/contact/" className="mil-btn mil-btn-border mil-up">
                  Contact Support
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      <CallToAction2 />
    </PlaxLayout>
  );
};

export default page;
