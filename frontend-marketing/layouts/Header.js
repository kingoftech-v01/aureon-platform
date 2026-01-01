"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const Header = ({ dark }) => {
  const currentPath = usePathname();
  const activeMenuFuntion = (value) =>
    value.some((el) => currentPath.includes(el)) ? "mil-active" : "";
  const [toggle, setToggle] = useState(false);

  return (
    <div className={`mil-top-panel ${dark ? "mil-dark-2" : ""}`}>
      <div className="container">
        <Link href="/" className="mil-logo">
          <span style={{
            fontSize: 24,
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            Aureon
          </span>
        </Link>
        <nav className={`mil-top-menu ${toggle ? "mil-active" : ""}`}>
          <ul>
            <li className={currentPath === "/" ? "mil-active" : ""}>
              <Link href="/">Home</Link>
            </li>
            <li className={`${activeMenuFuntion(["about"])}`}>
              <Link href="/about">About</Link>
            </li>
            <li className={`${activeMenuFuntion(["services"])}`}>
              <Link href="/services">Services</Link>
            </li>
            <li className={`${activeMenuFuntion(["price"])}`}>
              <Link href="/price">Pricing</Link>
            </li>
            <li className={`mil-has-children ${activeMenuFuntion(["blog", "publication"])}`}>
              <a href="#.">Resources</a>
              <ul>
                <li>
                  <Link href="/blog">Blog</Link>
                </li>
              </ul>
            </li>
            <li className={`${activeMenuFuntion(["contact"])}`}>
              <Link href="/contact">Contact</Link>
            </li>
          </ul>
        </nav>
        <div className="mil-menu-buttons">
          <a
            href="https://aureon.rhematek-solutions.com/accounts/login/"
            className="mil-btn mil-sm"
          >
            Log in
          </a>
          <a
            href="https://aureon.rhematek-solutions.com/accounts/signup/"
            className="mil-btn mil-sm mil-accent"
            style={{ marginLeft: 10 }}
          >
            Get Started
          </a>
          <div
            className={`mil-menu-btn ${toggle ? "mil-active" : ""}`}
            onClick={() => setToggle(!toggle)}
          >
            <span />
          </div>
        </div>
      </div>
    </div>
  );
};
export default Header;
