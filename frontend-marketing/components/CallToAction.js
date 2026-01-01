import Link from "next/link";

export const CallToAction1 = () => {
  return (
    <div className="mil-cta mil-up">
      <div className="container">
        <div className="mil-out-frame mil-visible mil-image mil-illustration-fix mil-p-160-0">
          <div className="row align-items-end">
            <div className="mil-text-center">
              <h2 className="mil-mb-30 mil-light mil-up">
                Automate Your Business, <br />
                Accelerate Your Growth
              </h2>
              <p className="mil-text-m mil-dark-soft mil-mb-60 mil-up">
                From contract creation to payment collection, <br />
                Aureon handles it all so you can focus on what matters.
              </p>
              <div className="mil-up mil-mb-60">
                <a
                  href="https://aureon.rhematek-solutions.com/accounts/signup/"
                  className="mil-btn mil-button-transform mil-md mil-add-arrow"
                >
                  Start Free Trial
                </a>
              </div>
            </div>
          </div>
          <div className="mil-illustration-absolute mil-type-2 mil-up">
            <img src="img/home-2/6.png" alt="Aureon Platform" />
          </div>
        </div>
      </div>
    </div>
  );
};

export const CallToAction2 = () => {
  return (
    <div className="mil-cta mil-up">
      <div className="container">
        <div
          className="mil-out-frame mil-p-160-160"
          style={{ backgroundImage: "url(img/home-3/5.png)" }}
        >
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-7 mil-sm-text-center">
              <h2 className="mil-light mil-mb-30 mil-up">
                Ready to Transform <br />
                Your Financial Workflows?
              </h2>
              <p className="mil-text-m mil-mb-60 mil-dark-soft mil-up">
                Join thousands of businesses using Aureon to <br />
                streamline contracts, invoices, and payments.
              </p>
              <div className="mil-buttons-frame mil-up">
                <a
                  href="https://aureon.rhematek-solutions.com/accounts/signup/"
                  className="mil-btn mil-md"
                >
                  Get Started Free
                </a>
                <Link href="/contact" className="mil-btn mil-border mil-md">
                  Contact Sales
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
