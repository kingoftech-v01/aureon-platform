import { PageBanner } from "@/components/Banner";
import { CallToAction2 } from "@/components/CallToAction";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
const page = () => {
  return (
    <PlaxLayout bg={false}>
      <PageBanner
        title="Adapted to your needs, discover what we have"
        pageName="Services"
      />

      {/* banner end */}
      {/* service */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-5 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Freedom to send, request money globally
              </h2>
              <p className="mil-text-m mil-soft mil-mb-30 mil-up">
                From sending money to friends and family to receiving payments
                from around the world, Plax Consumer offers you a simple and
                instant experience.
              </p>
              <div className="mil-up">
                <Link href="/price" className="mil-btn mil-m mil-add-arrow">
                  Pricing Plan
                </Link>
              </div>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <div className="mil-image-frame mil-up">
                <img
                  src="img/inner-pages/3.png"
                  alt="image"
                  className="mil-scale-img"
                  data-value-1={1}
                  data-value-2="1.2"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* service end */}
      {/* service */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row flex-sm-row-reverse justify-content-between align-items-center">
            <div className="col-xl-5 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Instant Financial Solutions for Global Businesses
              </h2>
              <p className="mil-text-m mil-soft mil-mb-30 mil-up">
                From instant and secure transactions to the flexibility to adapt
                to global needs, Plax Enterprise offers a reliable platform to
                drive your company's financial growth.
              </p>
              <div className="mil-up">
                <Link href="/price" className="mil-btn mil-m mil-add-arrow">
                  Pricing Plan
                </Link>
              </div>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <div className="mil-image-frame ml-up">
                <img
                  src="img/inner-pages/4.png"
                  alt="image"
                  className="mil-scale-img"
                  data-value-1={1}
                  data-value-2="1.2"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* service end */}
      {/* service */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-5 mil-mb-80">
              <h2 className="mil-mb-30 mil-up">
                Financial Innovation, discover the Plax Virtual Card
              </h2>
              <p className="mil-text-m mil-soft mil-mb-30 mil-up">
                Discover how this innovative tool boosts financial well-being
                and provides a safe and affordable alternative for financial
                inclusion in the region.
              </p>
              <div className="mil-up">
                <Link href="/price" className="mil-btn mil-m mil-add-arrow">
                  Pricing Plan
                </Link>
              </div>
            </div>
            <div className="col-xl-6 mil-mb-80">
              <div className="mil-image-frame mil-up">
                <img
                  src="img/inner-pages/5.png"
                  alt="image"
                  className="mil-scale-img"
                  data-value-1={1}
                  data-value-2="1.2"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* service end */}
      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-p-160-100">
            <div className="row justify-content-center mil-text-center">
              <div className="col-xl-8 mil-mb-80-adaptive-30">
                <h2 className="mil-up">
                  Innovation and Efficiency in Every Transaction
                </h2>
              </div>
            </div>
            <div className="row">
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/inner-pages/icons/4.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-20 mil-up">Simplicity in Every Step</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Experience the convenience of a simplified payment process,
                    from creating your account
                  </p>
                </div>
              </div>
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/inner-pages/icons/5.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-20 mil-up">
                    Guaranteed Advanced Security
                  </h5>
                  <p className="mil-text-m mil-soft mil-up">
                    We implement cutting-edge security measures to protect your
                    financial information at all times.
                  </p>
                </div>
              </div>
              <div className="col-xl-4 mil-mb-60">
                <div className="mil-icon-box">
                  <img
                    src="img/inner-pages/icons/6.svg"
                    alt="icon"
                    className="mil-mb-30 mil-up"
                  />
                  <h5 className="mil-mb-20 mil-up">Unparalleled Efficiency</h5>
                  <p className="mil-text-m mil-soft mil-up">
                    Fast, secure and reliable transactions that reflect our
                    commitment to excellence every step of the way.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}
      {/* quote */}
      <div className="mil-quote mil-p-160-130">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-10">
              <h2 className="mil-mb-30">
                "At Plax, transparency is not just a promise; It is the
                cornerstone of our relationship with you. We believe that trust
                is built with clear policies and coherent actions."
              </h2>
              <p className="mil-text-m mil-soft mil-mb-60">- Plax Team</p>
              <div className="row">
                <div className="col-xl-6">
                  <ul className="mil-list-2 mil-type-2 mil-mb-30">
                    <li>
                      <div className="mil-up">
                        <h5 className="mil-mb-15">Privacy policies</h5>
                        <p className="mil-text-m mil-soft">
                          Your privacy is our priority. We never share your
                          information with third parties without your express
                          consent.
                        </p>
                      </div>
                    </li>
                  </ul>
                </div>
                <div className="col-xl-6">
                  <ul className="mil-list-2 mil-type-2 mil-mb-30">
                    <li>
                      <div className="mil-up">
                        <h5 className="mil-mb-15">Data protection</h5>
                        <p className="mil-text-m mil-soft">
                          We are committed to protecting your personal and
                          financial data with the highest security measures
                        </p>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* quote end */}
      {/* call to action */}
      <CallToAction2 />
      {/* call to action end */}
    </PlaxLayout>
  );
};
export default page;
