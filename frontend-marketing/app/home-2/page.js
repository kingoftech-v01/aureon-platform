"use client";
import Banner from "@/components/Banner";
import { CallToAction2 } from "@/components/CallToAction";
import PlaxAccordion from "@/components/PlaxAccordion";
import Testimonials1 from "@/components/Testimonials";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";

const page = () => {
  return (
    <PlaxLayout bg={false}>
      <Banner
        title="Shop with Confidence, Protected"
        img="img/home-1/1.png"
        style={{ maxWidth: "125%", transform: "translateX(10%)" }}
      />
      {/* banner end */}
      {/* features */}
      <div className="mil-features mil-p-160-80">
        <div className="container">
          <div className="row flex-sm-row-reverse justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Exclusive Benefits of <br />
                Using Plax
              </h2>
              <ul className="mil-list-1">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15 mil-up">Instant Transactions</h5>
                    <p className="mil-text-m mil-soft mil-up">
                      Make money transfers immediately, without <br />
                      complications or delays.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15 mil-up">Guaranteed Security</h5>
                    <p className="mil-text-m mil-soft mil-up">
                      Protect your financial information with our advanced{" "}
                      <br />
                      security protocols.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15 mil-up">
                      Extensive Global Coverage
                    </h5>
                    <p className="mil-text-m mil-soft mil-up">
                      Access our global network that covers more than <br />
                      169 countries for your international transactions.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <div className="mil-image-frame mil-visible-overflow">
                <img src="img/home-1/2.png" alt="image" className="mil-up" />
                <div className="mil-img-box mil-accent-box mil-up">
                  <div>
                    <h2 className="mil-light mil-mb-15">100%</h2>
                    <p className="mil-text-s mil-light">
                      Security in your <br />
                      payments
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}
      {/* facts */}
      <div className="mil-facts mil-p-0-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-6">
              <div className="row">
                <div className="col-xl-6 mil-sm-text-center mil-mb-30 mil-up">
                  <p className="h1 mil-display mil-mb-15">
                    <span className="mil-accent mil-counter" data-number={7}>
                      7
                    </span>
                    <span className="mil-pale">m</span>
                  </p>
                  <h5>Registered Users</h5>
                </div>
                <div className="col-xl-6 mil-sm-text-center mil-mb-80 mil-up">
                  <p className="h1 mil-display mil-mb-15">
                    <span className="mil-accent mil-counter" data-number={170}>
                      170
                    </span>
                    <span className="mil-pale">+</span>
                  </p>
                  <h5>Countries with our coverage</h5>
                </div>
              </div>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <p className="mil-text-m mil-soft mil-up">
                Dive into the data behind Plax's success. From the number of
                users to the extent of our global network, these facts and
                figures highlight Plax's impact on the world of finance and how
                we have managed
              </p>
            </div>
          </div>
        </div>
      </div>
      {/* facts end */}
      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-p-160-100">
            <div className="row align-items-end">
              <div className="col-xl-8 mil-mb-80-adaptive-30">
                <h2 className="mil-up">
                  Innovation and Efficiency in Every Transaction
                </h2>
              </div>
              <div className="col-xl-4 mil-mb-80 mil-up">
                <Link
                  href="/services"
                  className="mil-btn mil-m mil-add-arrow mil-adaptive-right"
                >
                  Learn More
                </Link>
              </div>
            </div>
            <div className="row">
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/home-1/icons/1.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-30 mil-up">Unmatched Speed</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Make instant transfers and experience <br />
                    Plax's unparalleled speed with every transaction.
                  </p>
                </div>
              </div>
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/home-1/icons/2.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-30 mil-up">Extensive Global Network</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Connect with the world through our <br />
                    global network that spans more than <br />
                    170 countries.
                  </p>
                </div>
              </div>
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/home-1/icons/3.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-30 mil-up">Advanced Security</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Protect your assets with our robust <br />
                    security protocols and cutting-edge <br />
                    technologies.
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
                The Perfect Solution for Your Personal Transfers
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Explore the convenience of Plax Consumer and <br />
                make your personal transfers quick and easy.
              </p>
              <ul className="mil-list-2">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Intuitive Interface</h5>
                    <p className="mil-text-m mil-soft">
                      Enjoy a friendly user experience and navigate the <br />
                      application intuitively to carry out your transactions
                      with ease.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">First Level Security</h5>
                    <p className="mil-text-m mil-soft">
                      Protect your transfers and personal data with our advanced{" "}
                      <br />
                      security measures, giving you peace of mind with every
                      transaction.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <div className="mil-image-frame mil-visible-overflow">
                <img src="img/home-1/3.png" alt="image" className="mil-up" />
                <div className="mil-img-box mil-right-max mil-soft-box mil-up">
                  <img src="img/home-1/icons/4.svg" alt="icon" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}
      {/* testimonials */}
      <div className="mil-testimonials mil-p-0-160">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-7 mil-relative">
              <Testimonials1 />
            </div>
          </div>
        </div>
      </div>
      {/* testimonials end */}
      {/* brands */}
      <div className="mil-brands mil-p-0-160">
        <div className="container">
          <h5 className="mil-text-center mil-soft mil-mb-60 mil-up">
            Join over 7,000 satisfied customers who enjoy our service!
          </h5>
          <div className="row justify-content-center">
            <div className="col-6 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/1.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/2.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/3.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/4.svg" alt="brand" className="mil-up" />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* brands end */}
      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-bg-1">
            <div className="mil-gradient-plus" />
            <div className="row justify-content-between align-items-center">
              <div className="col-xl-7 mil-mt-60">
                <h2 className="mil-mb-30 mil-up">
                  Discover Plax today and Transform your Financial Experience!
                </h2>
                <p className="mil-text-m mil-mb-60 mil-up">
                  Discover the innovation, speed and security <br />
                  of Plax in every transaction.
                </p>
                <div className="mil-up">
                  <Link
                    href="register"
                    className="mil-btn mil-md mil-add-arrow"
                  >
                    Register now
                  </Link>
                </div>
              </div>
              <div className="col-xl-5 mil-mt-60">
                <img
                  src="img/home-1/5.png"
                  alt="img"
                  style={{ width: "100%" }}
                  className="mil-up"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}
      {/* faq */}
      <div className="mil-faq mil-p-160-130">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-8">
              <div className="mil-text-center">
                <h2 className="mil-mb-30 mil-up">
                  Explore Our Frequently <br />
                  Asked Questions
                </h2>
                <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                  Find quick and clear answers to the most common <br />
                  questions about Plax
                </p>
              </div>
              <PlaxAccordion />
            </div>
          </div>
        </div>
      </div>
      {/* faq end */}
      {/* call to action */}
      <CallToAction2 />
      {/* call to action end */}
    </PlaxLayout>
  );
};
export default page;
