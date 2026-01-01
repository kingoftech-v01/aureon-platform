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
          <img
            src={dark ? "img/logo-light.png" : "img/logo.png"}
            alt="Plax"
            width={83}
            height={32}
          />
        </Link>
        <nav className={`mil-top-menu ${toggle ? "mil-active" : ""}`}>
          <ul>
            <li
              className={`mil-has-children ${
                currentPath.includes("home") || currentPath == "/"
                  ? "mil-active"
                  : ""
              }`}
            >
              <a href="#.">Home</a>
              <ul>
                <li>
                  <Link href="/">Type 1</Link>
                </li>
                <li>
                  <Link href="home-2">Type 2</Link>
                </li>
                <li>
                  <Link href="home-3">Type 3</Link>
                </li>
                <li>
                  <Link href="home-4">Type 4</Link>
                </li>
                <li>
                  <Link href="home-5">Type 5</Link>
                </li>
              </ul>
            </li>
            <li className={`${activeMenuFuntion(["about"])}`}>
              <Link href="about">About</Link>
            </li>
            <li className={`${activeMenuFuntion(["services"])}`}>
              <Link href="services">Services</Link>
            </li>
            <li
              className={`mil-has-children ${activeMenuFuntion([
                "blog",
                "publication",
              ])}`}
            >
              <a href="#.">Blog</a>
              <ul>
                <li>
                  <Link href="blog">Blog list</Link>
                </li>
                <li>
                  <Link href="publication">Blog details</Link>
                </li>
              </ul>
            </li>
            <li className={`${activeMenuFuntion(["contact"])}`}>
              <Link href="contact">Contact</Link>
            </li>
            <li
              className={`mil-has-children ${activeMenuFuntion([
                "career",
                "price",
                "register",
              ])}`}
            >
              <a href="#.">Pages</a>
              <ul>
                <li>
                  <Link href="career">Career</Link>
                </li>
                <li>
                  <Link href="career-details">Career details</Link>
                </li>
                <li>
                  <Link href="price">Pricing</Link>
                </li>
                <li>
                  <Link href="register">Register</Link>
                </li>
              </ul>
            </li>
          </ul>
        </nav>
        <div className="mil-menu-buttons">
          <Link href="register" className="mil-btn mil-sm">
            Log in
          </Link>
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
