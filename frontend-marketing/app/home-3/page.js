import Banner from "@/components/Banner";
import { CallToAction1 } from "@/components/CallToAction";
import Testimonials1 from "@/components/Testimonials";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";

const page = () => {
  return (
    <PlaxLayout bg={false} margin={0}>
      <Banner
        title="Simplified International Payments"
        img="img/home-3/1.png"
        style={{ maxWidth: "140%", transform: "translateX(20%)" }}
      />
      {/* banner end */}
      {/* brands */}
      <div className="mil-brands mil-p-160-160">
        <div className="container">
          <h5 className="mil-text-center mil-soft mil-mb-60 mil-up">
            Join over 7,000 satisfied customers who enjoy our service!
          </h5>
          <div className="row justify-content-center">
            <div className="col-4 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/1.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-4 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/2.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-4 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/3.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-4 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/4.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-4 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/5.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-4 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/6.svg" alt="brand" className="mil-up" />
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
              <h2 className="mil-mb-30 mil-up">
                Tools that enhance your Financial control
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Visualize your financial progress with detailed reports and
                graphs <br />
                that give you visual insights into your spending and saving
                habits.
              </p>
              <ul className="mil-list-1">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15 mil-up">
                      Detailed Expense Tracking
                    </h5>
                    <p className="mil-text-m mil-soft mil-up">
                      Record each daily expense in detail and get precise <br />
                      insights into your cash flow.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15 mil-up">
                      Advanced Savings Management
                    </h5>
                    <p className="mil-text-m mil-soft mil-up">
                      Identify savings opportunities and maximize the <br />
                      accumulation of resources for your financial goals.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15 mil-up">Efficient Debt Control</h5>
                    <p className="mil-text-m mil-soft mil-up">
                      Manage your debts clearly and efficiently, avoiding <br />
                      unnecessary charges and improving.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <div className="mil-image-frame mil-visible-overflow">
                <img src="img/home-3/2.png" alt="image" className="mil-up" />
                <div className="mil-img-box mil-accent-box mil-up">
                  <img src="img/home-3/icons/1.svg" alt="icon" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}
      {/* features */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Your Finances in Your Hands with Plax
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Visualize your financial progress with detailed reports and
                graphs <br />
                that give you visual insights into your spending and saving
                habits.
              </p>
              <ul className="mil-list-2 mil-mb-60">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Detailed Reports and Graphics</h5>
                    <p className="mil-text-m mil-soft">
                      Visualize your financial progress with detailed <br />
                      reports and graphs that give you visual insights into{" "}
                      <br />
                      your spending and saving habits.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">
                      Intuitive and Friendly Interface
                    </h5>
                    <p className="mil-text-m mil-soft">
                      Our easy-to-use interface allows you to navigate <br />
                      Plax effortlessly, giving you an intuitive user
                      experience.
                    </p>
                  </div>
                </li>
              </ul>
              <div className="mil-up mil-mb-60">
                <Link
                  href="/about"
                  className="mil-btn mil-button-transform mil-m mil-add-arrow"
                >
                  Learn More
                </Link>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-80">
              <div className="mil-image-frame mil-image-frame-2 mil-visible-overflow">
                <img src="img/home-3/3.png" alt="image" className="mil-up" />
                <div className="mil-img-box mil-left-box mil-left-max mil-soft-box mil-up">
                  <img src="img/home-3/icons/2.svg" alt="icon" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}
      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-visible mil-image mil-p-160-130">
            <div className="row align-items-end">
              <div className="col-xl-8 mil-mb-80-adaptive-30">
                <h2 className="mil-up mil-light">
                  Discover wow Plax works to transform your Finances
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
              <div className="col-xl-4 mil-mb-30">
                <Link href="/about" className="mil-icon-box mil-center mil-hover">
                  <img
                    src="img/home-3/icons/3.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-20 mil-light mil-up">
                    Extensive Global Network
                  </h5>
                  <p className="mil-text-m mil-light mil-mb-30 mil-up">
                    Make instant transfers and experience Plax's unparalleled
                    speed with every transaction.
                  </p>
                  <div className="mil-link mil-accent mil-up">
                    More information
                  </div>
                </Link>
              </div>
              <div className="col-xl-4 mil-mb-30">
                <Link href="/career" className="mil-icon-box mil-center mil-hover">
                  <img
                    src="img/home-3/icons/4.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-20 mil-light mil-up">
                    Extensive Global Network
                  </h5>
                  <p className="mil-text-m mil-light mil-mb-30 mil-up">
                    Make instant transfers and experience Plax's unparalleled
                    speed with every transaction.
                  </p>
                  <div className="mil-link mil-accent mil-up">
                    More information
                  </div>
                </Link>
              </div>
              <div className="col-xl-4 mil-mb-30">
                <Link href="/pricing" className="mil-icon-box mil-center mil-hover">
                  <img
                    src="img/home-3/icons/5.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-20 mil-light mil-up">
                    Extensive Global Network
                  </h5>
                  <p className="mil-text-m mil-light mil-mb-30 mil-up">
                    Make instant transfers and experience Plax's unparalleled
                    speed with every transaction.
                  </p>
                  <div className="mil-link mil-accent mil-up">
                    More information
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}
      {/* features */}
      <div className="mil-features mil-p-160-80">
        <div className="container">
          <div className="row flex-sm-row-reverse justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Access Plax from any device, anytime
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                Visualize your financial progress with detailed reports and
                graphs <br />
                that give you visual insights into your spending and saving
                habits.
              </p>
              <ul className="mil-list-2">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Instant Sync</h5>
                    <p className="mil-text-m mil-soft">
                      Experience instant syncing between your devices, meaning
                      your data is always up to date, whether on your phone,
                      tablet or computer.
                    </p>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-mb-15">Universal Compatibility</h5>
                    <p className="mil-text-m mil-soft">
                      Enjoy Plax's universal compatibility across Android
                      devices, iOS devices and desktop platforms, ensuring a
                      seamless experience regardless of which device you prefer
                      to use.
                    </p>
                  </div>
                </li>
              </ul>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <div className="mil-image-frame mil-visible-overflow">
                <img src="img/home-3/4.png" alt="image" className="mil-up" />
                <div className="mil-img-box mil-soft-box mil-up">
                  <img src="img/home-3/icons/6.svg" alt="icon" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}
      {/* testimonials */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-bg-1 mil-p-160-160">
            <div className="row justify-content-center">
              <div className="col-xl-7 mil-relative">
                <Testimonials1 />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* testimonials end */}
      {/* facts */}
      <div className="mil-facts mil-p-160-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-6">
              <div className="row">
                <div className="col-xl-6 mil-sm-text-center mil-mb-30 mil-up">
                  <p className="h1 mil-display mil-mb-15">
                    <span className="mil-accent mil-counter" data-number={20}>
                      20
                    </span>
                    <span className="mil-pale">%</span>
                  </p>
                  <h5>Average Monthly Savings</h5>
                </div>
                <div className="col-xl-6 mil-sm-text-center mil-mb-80 mil-up">
                  <p className="h1 mil-display mil-mb-15">
                    <span className="mil-accent mil-counter" data-number={98}>
                      98
                    </span>
                    <span className="mil-pale">%</span>
                  </p>
                  <h5>Of Users Recommend Plax:</h5>
                </div>
              </div>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <p className="mil-text-m mil-soft mil-up">
                Plax has positively impacted the financial lives of over a
                million satisfied users around the world, and each time we
                reveal new milestones that we will share with great hysto with
                all our huge community
              </p>
            </div>
          </div>
        </div>
      </div>
      {/* facts end */}
      {/* call to action */}
      <CallToAction1 />
      {/* call to action end */}
    </PlaxLayout>
  );
};
export default page;
