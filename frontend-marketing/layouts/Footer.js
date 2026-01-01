"use client";
import Link from "next/link";
import { useState } from "react";
import { marketingApi } from "@/lib/api";

const Footer = ({ bg = true, margin = 160, footer }) => {
  switch (footer) {
    case 1:
      return <Footer1 bg={bg} margin={margin} />;
    case 2:
      return <Footer2 bg={bg} margin={margin} />;
    case 3:
      return <Footer3 bg={bg} margin={margin} />;

    default:
      return <Footer1 bg={bg} margin={margin} />;
  }
};
export default Footer;

const NewsletterForm = ({ darkText }) => {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState({ type: "", message: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    try {
      const response = await marketingApi.subscribeNewsletter(email);
      if (response && !response.error) {
        setStatus({ type: "success", message: "Subscribed!" });
        setEmail("");
      } else {
        setStatus({ type: "error", message: "Failed to subscribe" });
      }
    } catch (error) {
      setStatus({ type: "error", message: "Failed to subscribe" });
    } finally {
      setLoading(false);
      setTimeout(() => setStatus({ type: "", message: "" }), 3000);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mil-subscripe-form-footer">
      <input
        className="mil-input"
        name="EMAIL"
        type="email"
        placeholder="Email"
        autoComplete="off"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <button type="submit" disabled={loading}>
        <i className="far fa-envelope-open mil-dark" />
      </button>
      {status.message && (
        <p
          className={`mil-text-xs ${darkText ? "mil-soft" : "mil-pale"}`}
          style={{
            marginTop: 10,
            color: status.type === "success" ? "#22c55e" : "#ef4444",
          }}
        >
          {status.message}
        </p>
      )}
    </form>
  );
};

const Footer1 = ({ bg = true, margin = 160 }) => {
  return (
    <footer className={`${bg ? "mil-footer-with-bg" : ""} mil-p-${margin}-0 `}>
      <div className="container">
        <div className="row">
          <div className="col-xl-3">
            <Link href="/" className="mil-footer-logo mil-mb-60">
              <span
                style={{
                  fontSize: 28,
                  fontWeight: "bold",
                  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                Aureon
              </span>
            </Link>
          </div>
          <div className="col-xl-3 mil-mb-60">
            <h6 className="mil-mb-60">Useful Links</h6>
            <ul className="mil-footer-list">
              <li className="mil-text-m mil-soft mil-mb-15">
                <Link href="/">Home</Link>
              </li>
              <li className="mil-text-m mil-soft mil-mb-15">
                <Link href="/about">About Us</Link>
              </li>
              <li className="mil-text-m mil-soft mil-mb-15">
                <Link href="/contact">Contact Us</Link>
              </li>
              <li className="mil-text-m mil-soft mil-mb-15">
                <Link href="/services">Services</Link>
              </li>
              <li className="mil-text-m mil-soft mil-mb-15">
                <Link href="/price">Pricing</Link>
              </li>
            </ul>
          </div>
          <div className="col-xl-3 mil-mb-60">
            <h6 className="mil-mb-60">Contact</h6>
            <ul className="mil-footer-list">
              <li className="mil-text-m mil-soft mil-mb-15">
                Montreal, Quebec
                <br />
                Canada
              </li>
              <li className="mil-text-m mil-soft mil-mb-15">
                +1 (514) 555-0123
              </li>
              <li className="mil-text-m mil-soft mil-mb-15">
                hello@aureon.io
              </li>
            </ul>
          </div>
          <div className="col-xl-3 mil-mb-80">
            <h6 className="mil-mb-60">Newsletter</h6>
            <p className="mil-text-xs mil-soft mil-mb-15">
              Subscribe to get the latest news from us
            </p>
            <NewsletterForm darkText />
          </div>
        </div>
        <div className="mil-footer-bottom">
          <div className="row">
            <div className="col-xl-6">
              <p className="mil-text-s mil-soft">
                &copy; {new Date().getFullYear()} Aureon by Rhematek Solutions. All rights reserved.
              </p>
            </div>
            <div className="col-xl-6">
              <p className="mil-text-s mil-text-right mil-sm-text-left mil-soft">
                <Link href="/privacy">Privacy Policy</Link>
                {" | "}
                <Link href="/terms">Terms of Service</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

const Footer3 = ({ bg = true, margin = 160 }) => {
  return (
    <footer className="mil-footer-dark-2 mil-p-160-0">
      <div className="container">
        <div className="row">
          <div className="col-xl-3">
            <Link href="/" className="mil-footer-logo mil-mb-60">
              <span
                style={{
                  fontSize: 28,
                  fontWeight: "bold",
                  color: "white",
                }}
              >
                Aureon
              </span>
            </Link>
          </div>
          <div className="col-xl-3 mil-mb-60">
            <h6 className="mil-mb-60 mil-soft">Useful Links</h6>
            <ul className="mil-footer-list">
              <li className="mil-text-m mil-pale mil-mb-15">
                <Link href="/">Home</Link>
              </li>
              <li className="mil-text-m mil-pale mil-mb-15">
                <Link href="/about">About Us</Link>
              </li>
              <li className="mil-text-m mil-pale mil-mb-15">
                <Link href="/contact">Contact Us</Link>
              </li>
              <li className="mil-text-m mil-pale mil-mb-15">
                <Link href="/services">Services</Link>
              </li>
              <li className="mil-text-m mil-pale mil-mb-15">
                <Link href="/price">Pricing</Link>
              </li>
            </ul>
          </div>
          <div className="col-xl-3 mil-mb-60">
            <h6 className="mil-mb-60 mil-soft">Contact</h6>
            <ul className="mil-footer-list">
              <li className="mil-text-m mil-pale mil-mb-15">
                Montreal, Quebec
                <br />
                Canada
              </li>
              <li className="mil-text-m mil-pale mil-mb-15">
                +1 (514) 555-0123
              </li>
              <li className="mil-text-m mil-pale mil-mb-15">
                hello@aureon.io
              </li>
            </ul>
          </div>
          <div className="col-xl-3 mil-mb-80">
            <h6 className="mil-mb-60 mil-soft">Newsletter</h6>
            <p className="mil-text-xs mil-pale mil-mb-15">
              Subscribe to get the latest news from us
            </p>
            <NewsletterForm />
          </div>
        </div>
        <div className="mil-footer-bottom">
          <div className="row">
            <div className="col-xl-6">
              <p className="mil-text-s mil-pale">
                &copy; {new Date().getFullYear()} Aureon by Rhematek Solutions. All rights reserved.
              </p>
            </div>
            <div className="col-xl-6">
              <p className="mil-text-s mil-text-right mil-sm-text-left mil-pale">
                <Link href="/privacy">Privacy Policy</Link>
                {" | "}
                <Link href="/terms">Terms of Service</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

const Footer2 = () => {
  return (
    <footer className="mil-footer-dark mil-p-160-0">
      <div className="container">
        <div className="row">
          <div className="col-xl-9 mil-mb-60 mil-footer-space-fix">
            <Link href="/" className="mil-footer-logo mil-logo-2 mil-mb-60">
              <span
                style={{
                  fontSize: 28,
                  fontWeight: "bold",
                  color: "white",
                }}
              >
                Aureon
              </span>
            </Link>
            <ul className="mil-footer-list mil-footer-list-2">
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                <Link href="/">Home</Link>
              </li>
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                <Link href="/about">About Us</Link>
              </li>
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                <Link href="/contact">Contact Us</Link>
              </li>
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                <Link href="/services">Services</Link>
              </li>
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                <Link href="/price">Pricing</Link>
              </li>
            </ul>
          </div>
          <div className="col-xl-3 mil-mb-60">
            <ul className="mil-footer-list">
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                Montreal, Quebec
                <br />
                Canada
              </li>
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                +1 (514) 555-0123
              </li>
              <li className="mil-text-m mil-dark-soft mil-mb-15">
                hello@aureon.io
              </li>
            </ul>
          </div>
        </div>
        <div className="mil-footer-bottom">
          <div className="row">
            <div className="col-xl-6">
              <p className="mil-text-s mil-dark-soft">
                &copy; {new Date().getFullYear()} Aureon by Rhematek Solutions. All rights reserved.
              </p>
            </div>
            <div className="col-xl-6">
              <p className="mil-text-s mil-text-right mil-sm-text-left mil-dark-soft">
                <Link href="/privacy">Privacy Policy</Link>
                {" | "}
                <Link href="/terms">Terms of Service</Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};
