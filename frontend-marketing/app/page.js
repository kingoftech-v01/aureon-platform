"use client";
import Banner from "@/components/Banner";
import { CallToAction1 } from "@/components/CallToAction";
import { Testimonials2 } from "@/components/Testimonials";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
const page = () => {
  return (
    <PlaxLayout>
      {/* banner */}
      <Banner />
      {/* banner end */}
      {/* brands */}
      <div className="mil-brands mil-p-160-160">
        <div className="container">
          <h5 className="mil-text-center mil-soft mil-mb-60 mil-up">
            Join over 7,000 satisfied customers who enjoy our service!
          </h5>
          <div className="row justify-content-center">
            <div className="col-3 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/1.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-3 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/2.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-3 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/3.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-3 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/4.svg" alt="brand" className="mil-up" />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* brands end */}
      {/* features */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row flex-sm-row-reverse justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">Our essence, your experience</h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Visualize your financial progress with detailed reports and
                graphs <br />
                that give you visual insights into your spending and saving
                habits.
              </p>
              <ul className="mil-list-2 mil-type-2">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Plax® Global Service</h5>
                    <p className="mil-text-m mil-soft">
                      Experience exceptional service around the world. <br />
                      With our Plax® Global Service, we provide assistance{" "}
                      <br />
                      and support, wherever you are, to ensure your peace.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Personalized Rewards Program</h5>
                    <p className="mil-text-m mil-soft">
                      Enjoy a rewards program that fits your lifestyle. Earn{" "}
                      <br />
                      points with every purchase and access exclusive <br />
                      rewards, from trips to high-quality products.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <div className="mil-image-frame">
                <img src="img/home-2/2.png" alt="image" className="mil-up" />
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
                  Protected coverage on your <br />
                  purchases with Plax Standard
                </h2>
                <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                  Enjoy instant coverage against theft or accidental damage{" "}
                  <br />
                  for the first forty-five (45) days from the date of purchase.
                </p>
              </div>
            </div>
            <div className="mil-illustration-absolute mil-up">
              <img src="img/home-2/3.png" alt="illustration" />
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
                  alt="icon"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-up">Make your Purchase</h5>
                <p className="mil-text-s mil-soft mil-up">
                  Enjoy instant coverage against theft or accidental damage for
                  the first forty-five (45) days from the date of purchase.
                </p>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-with-bg mil-center mil-up">
                <img
                  src="img/home-2/icons/2.svg"
                  alt="icon"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-up">Manage your Rewards</h5>
                <p className="mil-text-s mil-soft mil-up">
                  Rewards easily, Access a personalized rewards program that
                  fits your lifestyle and preferences.
                </p>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-with-bg mil-center mil-up">
                <img
                  src="img/home-2/icons/3.svg"
                  alt="icon"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-up">Access Exclusive Benefits</h5>
                <p className="mil-text-s mil-soft mil-up">
                  From special offers to added security, every transaction is
                  not just a purchase, but an open door to a range.
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
                  Innovation and Efficiency in Every Transaction
                </h2>
              </div>
              <div className="col-xl-4 mil-mb-80 mil-up">
                <Link
                  href="register"
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
                Plax Standard unusual activity detection
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Keep track of your financial activity and the response to alert.{" "}
                <br />
                Your security is our priority, are always one step forward.
              </p>
              <ul className="mil-list-2 mil-type-2 mil-mb-60">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Connected device management</h5>
                    <p className="mil-text-m mil-soft">
                      Plax monitors the devices connected to your <br />
                      account. If we detect activity from a new device or <br />
                      an unusual change, we will notify you.
                    </p>
                  </div>
                </li>
              </ul>
              <div className="mil-up">
                <Link
                  href="/about"
                  className="mil-btn mil-button-transform mil-m mil-add-arrow"
                >
                  More Information
                </Link>
              </div>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <img
                src="img/home-2/4.png"
                alt="image"
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
                Instant Alerts &amp; Notifications with Plax
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Visualize your financial progress with detailed reports and
                graphs <br />
                that give you visual insights into your spending and saving
                habits.
              </p>
              <ul className="mil-list-2 mil-type-2">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Security in real time</h5>
                    <p className="mil-text-m mil-soft">
                      Notifications allow you to take immediate action in <br />
                      case of unauthorized transactions or unusual activities.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Notification History</h5>
                    <p className="mil-text-m mil-soft">
                      Keep track of your financial activity and the response to
                      alert. <br />
                      Your security is our priority, are always one step
                      forward.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <img
                src="img/home-2/5.png"
                alt="image"
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
          <Testimonials2 />
        </div>
      </div>
      {/* testimonials end */}
      {/* call to action */}
      <CallToAction1 />
    </PlaxLayout>
  );
};
export default page;
