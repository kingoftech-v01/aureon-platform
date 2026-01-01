import { ScrollSmoother, ScrollTrigger } from "@/lib/plugins";
import { gsap } from "gsap";
gsap.registerPlugin(ScrollTrigger, ScrollSmoother);
export const plaxUtility = {
  smoothScroll() {
    // ScrollSmoother.create({
    //   smooth: 1,
    //   effects: true,
    //   smoothTouch: 0.1,
    // });
    //ScrollTrigger.normalizeScroll(true);
  },
  scrollAnimations() {
    const appearance = document.querySelectorAll(".mil-up");

    appearance.forEach((section) => {
      gsap.fromTo(
        section,
        {
          opacity: 0,
          y: 50,
          scale: 0.98,
          ease: "sine",
        },
        {
          y: 0,
          opacity: 1,
          scale: 1,
          scrollTrigger: {
            trigger: section,
            toggleActions: "play none none reverse",
          },
        }
      );
    });

    const scaleImage = document.querySelectorAll(".mil-scale-img");
    scaleImage.forEach((section) => {
      // Use getAttribute to retrieve data attributes
      var value1 = section.getAttribute("data-value-1");
      var value2 = section.getAttribute("data-value-2");

      // Use the values as before in GSAP's fromTo method
      gsap.fromTo(
        section,
        {
          ease: "sine",
          scale: parseFloat(value1), // Ensure the value is treated as a number
        },
        {
          scale: parseFloat(value2), // Ensure the value is treated as a number
          scrollTrigger: {
            trigger: section,
            scrub: true,
            toggleActions: "play none none reverse",
          },
        }
      );
    });
  },
  preloader() {
    const preloaderTimeline = gsap.timeline();

    preloaderTimeline
      .to(".mil-preloader", {
        height: 0,
        ease: "sine",
        duration: 0.4,
        delay: "2.3",
      })
      .to(".mil-preloader .mil-load", {
        width: "calc(100% - 30px)",
        ease: "linear",
        duration: "1.3",
        delay: "-2.3",
      })
      .to(".mil-preloader .mil-load", {
        opacity: 0,
        ease: "sine",
        duration: "0.4",
        delay: "-0.6",
      })
      .to(".mil-preloader p", {
        scale: 0.5,
        opacity: 0,
        ease: "sine",
        duration: 0.4,
        delay: "-0.7",
        onComplete: function () {
          ScrollTrigger.refresh();
        },
      });
  },
  counters() {
    const numbers = document.querySelectorAll(".mil-counter");
    numbers.forEach((element) => {
      let zero = { val: 0 };
      let num = parseFloat(element.dataset.number);
      let split = num.toString().split(".");
      let decimals = split.length > 1 ? split[1].length : 0;

      gsap.to(zero, {
        val: num,
        duration: 1.8,
        scrollTrigger: {
          trigger: element,
          toggleActions: "play none none reverse",
        },
        onUpdate: function () {
          element.textContent = zero.val.toFixed(decimals);
        },
      });
    });
  },
  stickMenu() {
    ScrollTrigger.create({
      start: "top -70",
      end: 99999,
      toggleClass: {
        className: "mil-active",
        targets: ".mil-top-panel",
      },
    });
  },
  backToTop() {
    gsap.fromTo(
      ".progress-wrap",
      {
        yPercent: 100,
        autoAlpha: 0,
      },
      {
        yPercent: 0,
        autoAlpha: 1,
        scrollTrigger: {
          start: 500,
          toggleActions: "play none none reverse",
        },
      }
    );
  },
};
