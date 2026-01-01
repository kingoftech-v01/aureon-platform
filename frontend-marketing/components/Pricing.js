"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { marketingApi } from "@/lib/api";

// Default pricing data (fallback if API fails)
const defaultPlans = [
  {
    id: 1,
    name: "Starter",
    description: "Perfect for freelancers and small projects",
    price_monthly: 0,
    price_yearly: 0,
    features: ["Up to 5 contracts/month", "Basic invoicing", "Email support"],
    is_featured: false,
  },
  {
    id: 2,
    name: "Professional",
    description: "For growing businesses with more needs",
    price_monthly: 49,
    price_yearly: 39,
    features: ["Unlimited contracts", "Automated invoicing", "Priority support", "Custom branding"],
    is_featured: true,
  },
  {
    id: 3,
    name: "Enterprise",
    description: "For large teams requiring advanced features",
    price_monthly: 149,
    price_yearly: 119,
    features: ["Everything in Professional", "API access", "Dedicated account manager", "Custom integrations"],
    is_featured: false,
  },
];

const Pricing = () => {
  const [time, setTime] = useState("month");
  const [plans, setPlans] = useState(defaultPlans);

  useEffect(() => {
    const fetchPricing = async () => {
      try {
        const response = await marketingApi.getPricingPlans();
        if (response && response.data && response.data.length > 0) {
          setPlans(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch pricing:", error);
      }
    };
    fetchPricing();
  }, []);

  return (
    <div className="row justify-content-center">
      <div className="mil-switcher mil-mb-60 mil-up">
        <span
          className={`${time == "month" ? "mil-active" : ""}`}
          id="month"
          onClick={() => setTime("month")}
        >
          Monthly
        </span>
        <span
          className={`${time == "year" ? "mil-active" : ""}`}
          id="year"
          onClick={() => setTime("year")}
        >
          Yearly
        </span>
      </div>
      <div className="row">
        {plans.map((plan, index) => (
          <div className="col-md-4 col-sm-6" key={plan.id || index}>
            <div className={`mil-price-card ${plan.is_featured ? 'mil-featured' : ''} mil-up mil-mb-30`}>
              <h6 className={`${plan.is_featured ? 'mil-light' : ''} mil-mb-15`}>{plan.name}</h6>
              <p className={`mil-text-s ${plan.is_featured ? 'mil-dark-soft' : 'mil-soft'} mil-mb-30`}>
                {plan.description}
              </p>
              <h4 className={`${plan.is_featured ? 'mil-light' : ''} mil-mb-30`}>
                ${" "}
                <span
                  className={`mil-pricing-table-price ${plan.is_featured ? 'mil-light' : ''}`}
                  data-year-price={plan.price_yearly}
                  data-month-price={plan.price_monthly}
                >
                  {time == "year"
                    ? (plan.price_yearly || 0).toFixed(2)
                    : (plan.price_monthly || 0).toFixed(2)}
                </span>
                <span className={`mil-sup-text ${plan.is_featured ? 'mil-dark-soft' : 'mil-soft'}`}> / month</span>
              </h4>
              <Link href="/contact" className="mil-btn mil-m mil-fw mil-mb-30">
                {plan.price_monthly === 0 ? 'Get Started Free' : 'Choose Plan'}
              </Link>
              <ul className={`mil-text-mist mil-type-2 mil-check mil-text-s ${plan.is_featured ? 'mil-dark-soft' : 'mil-soft'} mil-mb-60`}>
                {(plan.features || []).map((feature, idx) => (
                  <li key={idx}>{feature}</li>
                ))}
              </ul>
              <Link href="/services" className="mil-link mil-accent">
                View all features
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
export default Pricing;

export const Pricing2 = () => {
  const [time, setTime] = useState("month");
  const [plans, setPlans] = useState(defaultPlans);

  useEffect(() => {
    const fetchPricing = async () => {
      try {
        const response = await marketingApi.getPricingPlans();
        if (response && response.data && response.data.length > 0) {
          setPlans(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch pricing:", error);
      }
    };
    fetchPricing();
  }, []);

  return (
    <div className="row justify-content-center">
      <div className="mil-switcher mil-mb-60 mil-up">
        <span
          className={`${time == "month" ? "mil-active" : ""}`}
          id="month"
          onClick={() => setTime("month")}
        >
          Monthly
        </span>
        <span
          className={`${time == "year" ? "mil-active" : ""}`}
          id="year"
          onClick={() => setTime("year")}
        >
          Yearly
        </span>
      </div>
      <div className="row">
        {plans.map((plan, index) => (
          <div className="col-md-4 col-sm-6" key={plan.id || index}>
            <div className={`mil-price-card ${plan.is_featured ? 'mil-featured' : ''} mil-up mil-mb-30`}>
              <h6 className="mil-light mil-mb-15">{plan.name}</h6>
              <p className="mil-text-s mil-dark-soft mil-mb-30">
                {plan.description}
              </p>
              <h4 className="mil-light mil-mb-30">
                ${" "}
                <span
                  className="mil-pricing-table-price mil-light"
                  data-year-price={plan.price_yearly}
                  data-month-price={plan.price_monthly}
                >
                  {time == "year"
                    ? (plan.price_yearly || 0).toFixed(2)
                    : (plan.price_monthly || 0).toFixed(2)}
                </span>
                <span className="mil-sup-text mil-soft"> / month</span>
              </h4>
              <Link href="/contact" className="mil-btn mil-m mil-fw mil-mb-30">
                {plan.price_monthly === 0 ? 'Get Started Free' : 'Choose Plan'}
              </Link>
              <ul className="mil-text-list mil-check mil-type-2 mil-text-s mil-dark-soft mil-mb-60">
                {(plan.features || []).map((feature, idx) => (
                  <li className="mil-dark-soft" key={idx}>{feature}</li>
                ))}
              </ul>
              <Link href="/services" className="mil-link mil-accent">
                View all features
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
