"use client";
import Link from "next/link";
import { useState } from "react";

const Pricing = () => {
  const [time, setTime] = useState("month");
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
        <div className="col-md-4 col-sm-6">
          <div className="mil-price-card mil-up mil-mb-30">
            <h6 className="mil-mb-15">Plax Consumer</h6>
            <p className="mil-text-s mil-soft mil-mb-30">
              Sending and receiving money in up to 5 countries
            </p>
            <h4 className="mil-mb-30">
              ${" "}
              <span
                className="mil-pricing-table-price"
                data-year-price={0.0}
                data-month-price={0.0}
              >
                {time == "year" ? "0.00" : "0.00"}
              </span>
              <span className="mil-sup-text mil-soft"> / month</span>
            </h4>
            <Link href="contact" className="mil-btn mil-m mil-fw mil-mb-30">
              Choose a plan
            </Link>
            <ul className="mil-text-mist mil-type-2 mil-check mil-text-s mil-soft mil-mb-60">
              <li>Unlimited transactions</li>
              <li>Basic Technical Support (Email)</li>
              <li>Instructional advisor</li>
            </ul>
            <a href="#." className="mil-link mil-accent">
              View all features
            </a>
          </div>
        </div>
        <div className="col-md-4 col-sm-6">
          <div className="mil-price-card mil-featured mil-up mil-mb-30">
            <h6 className="mil-light mil-mb-15">Plax Business</h6>
            <p className="mil-text-s mil-dark-soft mil-mb-30">
              Access to multi-currency accounts and local payments
            </p>
            <h4 className="mil-light mil-mb-30">
              ${" "}
              <span
                className="mil-light mil-pricing-table-price"
                data-year-price="9.99"
                data-month-price="14.99"
              >
                {time == "year" ? "9.99" : "14.99"}
              </span>
              <span className="mil-sup-text mil-dark-soft"> / month</span>
            </h4>
            <Link href="contact" className="mil-btn mil-m mil-fw mil-mb-30">
              Choose a plan
            </Link>
            <ul className="mil-text-mist mil-type-2 mil-check mil-text-s mil-dark-soft mil-mb-60">
              <li>Unlimited transactions</li>
              <li>Basic Technical Support (Email)</li>
              <li>Instructional advisor</li>
            </ul>
            <a href="#." className="mil-link mil-accent">
              View all features
            </a>
          </div>
        </div>
        <div className="col-md-4 col-sm-6">
          <div className="mil-price-card mil-up mil-mb-30">
            <h6 className="mil-mb-15">Plax Enterprise</h6>
            <p className="mil-text-s mil-soft mil-mb-30">
              Secure and reliable transactions at the enterprise level
            </p>
            <h4 className="mil-mb-30">
              ${" "}
              <span
                className="mil-pricing-table-price"
                data-year-price="34.99"
                data-month-price={49.0}
              >
                {time == "year" ? "34.99" : "49.00"}
              </span>
              <span className="mil-sup-text mil-soft"> / month</span>
            </h4>
            <Link href="contact" className="mil-btn mil-m mil-fw mil-mb-30">
              Choose a plan
            </Link>
            <ul className="mil-text-mist mil-type-2 mil-check mil-text-s mil-soft mil-mb-60">
              <li>Unlimited transactions</li>
              <li>Basic Technical Support (Email)</li>
              <li>Instructional advisor</li>
            </ul>
            <a href="#." className="mil-link mil-accent">
              View all features
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Pricing;

export const Pricing2 = () => {
  const [time, setTime] = useState("month");
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
        <div className="col-md-4 col-sm-6">
          <div className="mil-price-card mil-up mil-mb-30">
            <h6 className="mil-light mil-mb-15">Plax Consumer</h6>
            <p className="mil-text-s mil-dark-soft mil-mb-30">
              Sending and receiving money in up to 5 countries
            </p>
            <h4 className="mil-light mil-mb-30">
              ${" "}
              <span
                className="mil-pricing-table-price mil-light"
                data-year-price={0.0}
                data-month-price={0.0}
              >
                {time == "year" ? "0.00" : "0.00"}
              </span>
              <span className="mil-sup-text mil-soft"> / month</span>
            </h4>
            <Link href="contact" className="mil-btn mil-m mil-fw mil-mb-30">
              Choose a plan
            </Link>
            <ul className="mil-text-list mil-check mil-type-2 mil-text-s mil-dark-soft mil-mb-60">
              <li className="mil-dark-soft">Unlimited transactions</li>
              <li className="mil-dark-soft">Basic Technical Support (Email)</li>
              <li className="mil-dark-soft">Instructional advisor</li>
            </ul>
            <a href="#." className="mil-link mil-accent">
              View all features
            </a>
          </div>
        </div>
        <div className="col-md-4 col-sm-6">
          <div className="mil-price-card mil-featured mil-up mil-mb-30">
            <h6 className="mil-light mil-mb-15">Plax Business</h6>
            <p className="mil-text-s mil-dark-soft mil-mb-30">
              Access to multi-currency accounts and local payments
            </p>
            <h4 className="mil-light mil-mb-30">
              ${" "}
              <span
                className="mil-light mil-pricing-table-price"
                data-year-price="9.99"
                data-month-price="14.99"
              >
                {time == "year" ? "9.99" : "14.99"}
              </span>
              <span className="mil-sup-text mil-soft"> / month</span>
            </h4>
            <Link href="contact" className="mil-btn mil-m mil-fw mil-mb-30">
              Choose a plan
            </Link>
            <ul className="mil-text-list mil-check mil-type-2 mil-text-s mil-dark-soft mil-mb-60">
              <li>Unlimited transactions</li>
              <li>Basic Technical Support (Email)</li>
              <li>Instructional advisor</li>
            </ul>
            <a href="#." className="mil-link mil-accent">
              View all features
            </a>
          </div>
        </div>
        <div className="col-md-4 col-sm-6">
          <div className="mil-price-card mil-up mil-mb-30">
            <h6 className="mil-light mil-mb-15">Plax Enterprise</h6>
            <p className="mil-text-s mil-dark-soft mil-mb-30">
              Secure and reliable transactions at the enterprise level
            </p>
            <h4 className="mil-light mil-mb-30">
              ${" "}
              <span
                className="mil-pricing-table-price mil-light"
                data-year-price="34.99"
                data-month-price={49.0}
              >
                {time == "year" ? "49.0" : "34.99"}
              </span>
              <span className="mil-sup-text mil-soft"> / month</span>
            </h4>
            <Link href="contact" className="mil-btn mil-m mil-fw mil-mb-30">
              Choose a plan
            </Link>
            <ul className="mil-text-list mil-check mil-type-2 mil-text-s mil-dark-soft mil-mb-60">
              <li>Unlimited transactions</li>
              <li>Basic Technical Support (Email)</li>
              <li>Instructional advisor</li>
            </ul>
            <a href="#." className="mil-link mil-accent">
              View all features
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
