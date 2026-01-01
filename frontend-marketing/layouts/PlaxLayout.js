"use client";
import EmbedPopup from "@/components/EmbedPopup";
import { plaxUtility } from "@/utility";
import { Fragment, useEffect } from "react";
import Footer from "./Footer";
import Header from "./Header";
import ScrollProgress from "./ScrollProgress";

const PlaxLayout = ({ children, bg, margin, noFooter, dark, footer }) => {
  useEffect(() => {
    plaxUtility.scrollAnimations();
    plaxUtility.smoothScroll();
    plaxUtility.counters();
    plaxUtility.stickMenu();
    plaxUtility.backToTop();
  }, []);

  return (
    <Fragment>
      <EmbedPopup />
      <div id="smooth-wrapper" className="mil-wrapper">
        {/* scroll progress */}
        <ScrollProgress />
        {/* scroll progress end */}
        {/* back to top */}
        <a href="#" className="progress-wrap active-progress" />
        {/* top panel end */}
        <Header dark={dark} />
        {/* top panel end */}
        {/* content */}
        <div id="smooth-content">
          {children}
          {/* footer */}
          {!noFooter && <Footer footer={footer} bg={bg} margin={margin} dark />}
          {/* footer end */}
        </div>
        {/* content end */}
      </div>
    </Fragment>
  );
};
export default PlaxLayout;
